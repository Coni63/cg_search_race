//! Beam search guided by rollouts ("pilot method").
//!
//! Every node of the beam is evaluated by the finish time obtained when a simple
//! parametric controller drives the car from this node to the end of the race.
//! The best complete trajectory ever seen (the incumbent) is re-injected at every
//! depth, so the result can only improve over the initial solution.

use crate::sim::*;
use std::collections::HashSet;
use std::rc::Rc;

const RAD2DEG: f64 = 180.0 / std::f64::consts::PI;

/// atan2 approximation (max error ~1e-5 rad), enough for the controller
#[inline]
pub fn fast_atan2(y: f64, x: f64) -> f64 {
    let ax = x.abs();
    let ay = y.abs();
    let (mn, mx) = if ax < ay { (ax, ay) } else { (ay, ax) };
    if mx == 0.0 {
        return 0.0;
    }
    let a = mn / mx;
    let s = a * a;
    let mut r = ((((-0.0117212 * s + 0.05265332) * s - 0.11643287) * s + 0.19354346) * s - 0.33262347) * s + 0.99997726;
    r *= a;
    if ay > ax {
        r = std::f64::consts::FRAC_PI_2 - r;
    }
    if x < 0.0 {
        r = std::f64::consts::PI - r;
    }
    if y < 0.0 {
        -r
    } else {
        r
    }
}

pub struct Rng(u64);
impl Rng {
    pub fn new(seed: u64) -> Rng {
        Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1)
    }
    pub fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }
    pub fn f(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
    pub fn range(&mut self, lo: f64, hi: f64) -> f64 {
        lo + (hi - lo) * self.f()
    }
}

/// Parameters of the rollout controller
#[derive(Clone, Copy, Debug)]
pub struct Policy {
    /// aim at `target - kv * velocity`
    pub kv: f64,
    /// switch to the next checkpoint when the segment [pos, pos + ksw * velocity] enters the current one
    pub ksw: f64,
    /// radius used for the switch test
    pub rsw: f64,
    /// remaining angle (deg) above which we stop thrusting
    pub cut: f64,
    /// thrust used when the remaining angle is above `cut`
    pub low: i32,
    /// aim at a point shifted by `off` from the checkpoint center toward the following checkpoint
    pub off: f64,
}

impl Policy {
    pub fn random(rng: &mut Rng) -> Policy {
        Policy {
            kv: rng.range(0.0, 4.5),
            ksw: rng.range(0.0, 8.0),
            rsw: rng.range(200.0, 700.0),
            cut: rng.range(20.0, 120.0),
            low: if rng.f() < 0.5 { 0 } else { (rng.range(0.0, 200.0)) as i32 },
            off: if rng.f() < 0.3 { 0.0 } else { rng.range(0.0, 560.0) },
        }
    }

    pub fn mutate(&self, rng: &mut Rng, amp: f64) -> Policy {
        let mut p = *self;
        p.kv = (p.kv + rng.range(-1.0, 1.0) * 0.5 * amp).clamp(0.0, 6.0);
        p.ksw = (p.ksw + rng.range(-1.0, 1.0) * 0.8 * amp).clamp(0.0, 10.0);
        p.rsw = (p.rsw + rng.range(-1.0, 1.0) * 80.0 * amp).clamp(100.0, 900.0);
        p.cut = (p.cut + rng.range(-1.0, 1.0) * 15.0 * amp).clamp(5.0, 180.0);
        p.low = (p.low as f64 + rng.range(-1.0, 1.0) * 40.0 * amp).clamp(0.0, 200.0) as i32;
        p.off = (p.off + rng.range(-1.0, 1.0) * 80.0 * amp).clamp(0.0, 590.0);
        p
    }

    #[inline]
    pub fn act(&self, g: &Game, s: &State) -> Action {
        let x = s.x as f64;
        let y = s.y as f64;
        let vx = s.vx as f64;
        let vy = s.vy as f64;
        let mut idx = s.cp as usize;
        let cp = g.cps[idx];
        // distance from cp to the segment [p, p + ksw*v]
        let ex = vx * self.ksw;
        let ey = vy * self.ksw;
        let l2 = ex * ex + ey * ey;
        let mut u = if l2 > 0.0 { ((cp.0 - x) * ex + (cp.1 - y) * ey) / l2 } else { 0.0 };
        u = u.clamp(0.0, 1.0);
        let fx = x + ex * u - cp.0;
        let fy = y + ey * u - cp.1;
        if fx * fx + fy * fy < self.rsw * self.rsw && idx + 1 < g.last as usize {
            idx += 1;
        }
        let mut t = g.cps[idx];
        if self.off > 0.0 && idx + 1 < g.last as usize {
            let n = g.cps[idx + 1];
            let (nx, ny) = (n.0 - t.0, n.1 - t.1);
            let d = (nx * nx + ny * ny).sqrt();
            t = (t.0 + nx / d * self.off, t.1 + ny / d * self.off);
        }
        let dx = t.0 - vx * self.kv - x;
        let dy = t.1 - vy * self.kv - y;
        let desired = fast_atan2(dy, dx) * RAD2DEG;
        let mut diff = desired - s.angle as f64;
        while diff > 180.0 {
            diff -= 360.0;
        }
        while diff <= -180.0 {
            diff += 360.0;
        }
        let rot = ((diff + 0.5).floor() as i32).clamp(-18, 18);
        let rem = (diff - rot as f64).abs();
        let thrust = if rem > self.cut { self.low } else { 200 };
        Action { thrust, angle: rot }
    }

    /// Drive until the end. Returns the absolute finish time (turn index + t),
    /// or a large penalty if it does not finish before `limit` turns.
    #[inline]
    pub fn rollout(&self, g: &Game, s0: &State, limit: usize) -> f64 {
        let mut s = *s0;
        while (s.turn as usize) < limit {
            let a = self.act(g, &s);
            let t = g.step(&mut s, a);
            if s.cp == g.last {
                return (s.turn - 1) as f64 + t.unwrap();
            }
        }
        10000.0 - 100.0 * s.cp as f64
    }

    pub fn rollout_actions(&self, g: &Game, s0: &State) -> Vec<Action> {
        let mut s = *s0;
        let mut out = vec![];
        while (s.turn as usize) < MAX_TURN {
            let a = self.act(g, &s);
            out.push(a);
            g.step(&mut s, a);
            if s.cp == g.last {
                break;
            }
        }
        out
    }
}

/// Any closed-loop controller usable for rollouts
pub trait Ctrl: Sync {
    fn ctrl_act(&self, g: &Game, s: &State) -> Action;

    /// absolute finish time from s0, or a large penalty if not finished before `limit`
    fn ctrl_rollout(&self, g: &Game, s0: &State, limit: usize) -> f64 {
        let mut s = *s0;
        while (s.turn as usize) < limit {
            let a = self.ctrl_act(g, &s);
            let t = g.step(&mut s, a);
            if s.cp == g.last {
                return (s.turn - 1) as f64 + t.unwrap();
            }
        }
        10000.0 - 100.0 * s.cp as f64
    }

    fn ctrl_actions(&self, g: &Game, s0: &State) -> Vec<Action> {
        let mut s = *s0;
        let mut out = vec![];
        while (s.turn as usize) < MAX_TURN {
            let a = self.ctrl_act(g, &s);
            out.push(a);
            g.step(&mut s, a);
            if s.cp == g.last {
                break;
            }
        }
        out
    }
}

impl Ctrl for Policy {
    fn ctrl_act(&self, g: &Game, s: &State) -> Action {
        self.act(g, s)
    }
}

/// Find a few good controllers for this map (evaluated from the start).
pub fn tune_policies(g: &Game, rng: &mut Rng, n_random: usize, n_keep: usize) -> Vec<(f64, Policy)> {
    let mut pool: Vec<(f64, Policy)> = (0..n_random)
        .map(|_| {
            let p = Policy::random(rng);
            (p.rollout(g, &g.start, MAX_TURN), p)
        })
        .collect();
    pool.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    pool.truncate(n_keep * 4);
    // local refinement of each kept controller
    for item in pool.iter_mut() {
        for k in 0..300 {
            let amp = 1.0 - k as f64 / 300.0;
            let p = item.1.mutate(rng, amp.max(0.05));
            let f = p.rollout(g, &g.start, MAX_TURN);
            if f <= item.0 {
                *item = (f, p);
            }
        }
    }
    pool.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    pool.truncate(n_keep);
    pool
}

/// persistent list of actions
struct Hist {
    a: Action,
    parent: Option<Rc<Hist>>,
}

fn hist_to_vec(h: &Option<Rc<Hist>>) -> Vec<Action> {
    let mut out = vec![];
    let mut cur = h.clone();
    while let Some(n) = cur {
        out.push(n.a);
        cur = n.parent.clone();
    }
    out.reverse();
    out
}

#[derive(Clone)]
struct Node {
    s: State,
    h: Option<Rc<Hist>>,
    f: f64,
}

pub struct Incumbent {
    pub actions: Vec<Action>,
    pub score: f64,
    states: Vec<State>,
}

impl Incumbent {
    pub fn new(g: &Game, actions: Vec<Action>) -> Incumbent {
        let score = g.score(&actions);
        let mut states = vec![g.start];
        let mut s = g.start;
        for a in &actions {
            g.step(&mut s, *a);
            states.push(s);
            if s.cp == g.last {
                break;
            }
        }
        let n = states.len() - 1;
        Incumbent { actions: actions[..n].to_vec(), score, states }
    }
}

pub struct BeamParams {
    pub width: usize,
    pub angles: Vec<i32>,
    pub thrusts: Vec<i32>,
    pub noise: f64,
}

fn key(s: &State) -> (i32, i32, i32, i32, i32, u16) {
    (s.x, s.y, s.vx, s.vy, s.angle, s.cp)
}

pub fn beam(g: &Game, policies: &[&dyn Ctrl], inc: &mut Incumbent, bp: &BeamParams, rng: &mut Rng) {
    let mut beam = vec![Node { s: g.start, h: None, f: inc.score }];
    let mut depth = 0usize;
    while !beam.is_empty() && depth < inc.states.len() {
        let limit = (inc.score.ceil() as usize + 2).min(MAX_TURN);
        let mut seen: HashSet<(i32, i32, i32, i32, i32, u16)> = HashSet::with_capacity(beam.len() * 80);
        let mut children: Vec<Node> = Vec::with_capacity(beam.len() * 80);
        let mut best_child: Option<(f64, usize, usize)> = None;

        for node in beam.iter() {
            if node.s.cp == g.last {
                continue;
            }
            let mut acts: Vec<Action> = Vec::with_capacity(bp.angles.len() * bp.thrusts.len() + policies.len());
            for &a in &bp.angles {
                for &t in &bp.thrusts {
                    acts.push(Action { thrust: t, angle: a });
                }
            }
            for p in policies {
                acts.push(p.ctrl_act(g, &node.s));
            }
            for a in acts {
                let mut s = node.s;
                let t = g.step(&mut s, a);
                if !seen.insert(key(&s)) {
                    continue;
                }
                let h = Some(Rc::new(Hist { a, parent: node.h.clone() }));
                if s.cp == g.last {
                    let f = (s.turn - 1) as f64 + t.unwrap();
                    if f < inc.score {
                        *inc = Incumbent::new(g, hist_to_vec(&h));
                    }
                    continue;
                }
                let mut f = f64::INFINITY;
                let mut pi = 0;
                for (i, p) in policies.iter().enumerate() {
                    let r = p.ctrl_rollout(g, &s, limit);
                    if r < f {
                        f = r;
                        pi = i;
                    }
                }
                if best_child.map_or(true, |b| f < b.0) {
                    best_child = Some((f, children.len(), pi));
                }
                children.push(Node { s, h, f: f + bp.noise * rng.f() });
            }
        }

        // new incumbent from a rollout ?
        if let Some((f, ci, pi)) = best_child {
            if f < inc.score {
                let mut acts = hist_to_vec(&children[ci].h);
                acts.extend(policies[pi].ctrl_actions(g, &children[ci].s));
                let cand = Incumbent::new(g, acts);
                if cand.score < inc.score {
                    *inc = cand;
                }
            }
        }

        depth += 1;
        // keep the best `width` children
        if children.len() > bp.width {
            children.select_nth_unstable_by(bp.width, |a, b| a.f.partial_cmp(&b.f).unwrap());
            children.truncate(bp.width);
        }
        // re-inject the incumbent
        if depth + 1 < inc.states.len() {
            let s = inc.states[depth];
            if !children.iter().any(|c| key(&c.s) == key(&s)) {
                let mut h: Option<Rc<Hist>> = None;
                for a in &inc.actions[..depth] {
                    h = Some(Rc::new(Hist { a: *a, parent: h }));
                }
                children.push(Node { s, h, f: inc.score });
            }
        }
        beam = children;
    }
}

/// Plain wide beam search with a geometric heuristic (no rollout).
/// h = checkpoints * 1e6 - dist(next cp) + w_v * (velocity . unit(dir to next cp))
pub fn wide_beam(g: &Game, width: usize, angles: &[i32], thrusts: &[i32], w_v: f64) -> (f64, Vec<Action>) {
    struct WNode {
        s: State,
        h: Option<Rc<Hist>>,
        f: f64,
    }
    let heur = |s: &State| -> f64 {
        let c = g.cps[s.cp as usize];
        let dx = c.0 - s.x as f64;
        let dy = c.1 - s.y as f64;
        let d = (dx * dx + dy * dy).sqrt().max(1.0);
        s.cp as f64 * 1e6 - d + w_v * (s.vx as f64 * dx + s.vy as f64 * dy) / d
    };
    let mut beam = vec![WNode { s: g.start, h: None, f: 0.0 }];
    let mut best: (f64, Vec<Action>) = (f64::INFINITY, vec![]);
    let mut seen: HashSet<(i32, i32, i32, i32, i32, u16)> = HashSet::new();
    for _depth in 0..MAX_TURN {
        if beam.is_empty() || (beam[0].s.turn as f64) > best.0 {
            break;
        }
        seen.clear();
        let mut children = Vec::with_capacity(beam.len() * angles.len() * thrusts.len());
        for node in &beam {
            for &a in angles {
                for &t in thrusts {
                    let act = Action { thrust: t, angle: a };
                    let mut s = node.s;
                    let tt = g.step(&mut s, act);
                    if !seen.insert(key(&s)) {
                        continue;
                    }
                    let h = Some(Rc::new(Hist { a: act, parent: node.h.clone() }));
                    if s.cp == g.last {
                        let f = (s.turn - 1) as f64 + tt.unwrap();
                        if f < best.0 {
                            best = (f, hist_to_vec(&h));
                        }
                        continue;
                    }
                    children.push(WNode { f: -heur(&s), s, h });
                }
            }
        }
        if children.len() > width {
            children.select_nth_unstable_by(width, |a, b| a.f.partial_cmp(&b.f).unwrap());
            children.truncate(width);
        }
        beam = children;
    }
    best
}
