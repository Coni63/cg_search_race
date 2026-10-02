//! Closed-loop controller with one set of parameters per checkpoint, optimised by SA.
//!
//! For checkpoint j the car aims at `cp_j + (ox, oy) - kv * v`, switches to j+1
//! when its projected path enters a circle of radius `rsw` around cp_j, and stops
//! thrusting when the remaining angle is above `cut`.

use crate::search::{fast_atan2, Ctrl, Rng};
use crate::sim::*;

const RAD2DEG: f64 = 180.0 / std::f64::consts::PI;
pub const NP: usize = 7;

#[derive(Clone)]
pub struct SegPolicy {
    /// per checkpoint: ox, oy, kv, ksw, rsw, cut, low
    pub p: Vec<[f64; NP]>,
}

const LO: [f64; NP] = [-1500.0, -1500.0, 0.0, 0.0, 50.0, 0.0, 0.0];
const HI: [f64; NP] = [1500.0, 1500.0, 7.0, 10.0, 900.0, 180.0, 200.0];
const STEP: [f64; NP] = [150.0, 150.0, 0.5, 0.8, 80.0, 15.0, 40.0];

impl SegPolicy {
    pub fn uniform(g: &Game, kv: f64, ksw: f64, rsw: f64, cut: f64, low: f64) -> SegPolicy {
        SegPolicy { p: vec![[0.0, 0.0, kv, ksw, rsw, cut, low]; g.last as usize] }
    }

    #[inline]
    fn target(&self, g: &Game, s: &State) -> (usize, f64, f64) {
        let mut idx = s.cp as usize;
        let p = &self.p[idx];
        let cp = g.cps[idx];
        let (x, y, vx, vy) = (s.x as f64, s.y as f64, s.vx as f64, s.vy as f64);
        let ex = vx * p[3];
        let ey = vy * p[3];
        let l2 = ex * ex + ey * ey;
        let u = if l2 > 0.0 { (((cp.0 - x) * ex + (cp.1 - y) * ey) / l2).clamp(0.0, 1.0) } else { 0.0 };
        let fx = x + ex * u - cp.0;
        let fy = y + ey * u - cp.1;
        if fx * fx + fy * fy < p[4] * p[4] && idx + 1 < g.last as usize {
            idx += 1;
        }
        let q = &self.p[idx];
        let c = g.cps[idx];
        (idx, c.0 + q[0] - vx * q[2], c.1 + q[1] - vy * q[2])
    }

    #[inline]
    pub fn act(&self, g: &Game, s: &State) -> Action {
        let (idx, tx, ty) = self.target(g, s);
        let q = &self.p[idx];
        let desired = fast_atan2(ty - s.y as f64, tx - s.x as f64) * RAD2DEG;
        let mut diff = desired - s.angle as f64;
        while diff > 180.0 {
            diff -= 360.0;
        }
        while diff <= -180.0 {
            diff += 360.0;
        }
        let rot = ((diff + 0.5).floor() as i32).clamp(-18, 18);
        let rem = (diff - rot as f64).abs();
        let thrust = if rem > q[5] { q[6] as i32 } else { 200 };
        Action { thrust, angle: rot }
    }

    pub fn actions(&self, g: &Game) -> Vec<Action> {
        let mut s = g.start;
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

    /// Full rollout recording, for each checkpoint c, the first state whose target is c.
    fn rollout_cache(&self, g: &Game, first: &mut Vec<State>) -> f64 {
        first.clear();
        let mut s = g.start;
        first.push(s);
        while (s.turn as usize) < MAX_TURN {
            let a = self.act(g, &s);
            let t = g.step(&mut s, a);
            while first.len() <= s.cp as usize {
                first.push(s);
            }
            if s.cp == g.last {
                return (s.turn - 1) as f64 + t.unwrap();
            }
        }
        10000.0 - 100.0 * s.cp as f64
    }

    #[inline]
    fn rollout_from(&self, g: &Game, s0: State, limit: f64) -> f64 {
        let mut s = s0;
        while (s.turn as usize) < MAX_TURN && (s.turn as f64) <= limit + 1.0 {
            let a = self.act(g, &s);
            let t = g.step(&mut s, a);
            if s.cp == g.last {
                return (s.turn - 1) as f64 + t.unwrap();
            }
        }
        10000.0 - 100.0 * s.cp as f64
    }

    /// SA over the parameters. Returns the best score.
    pub fn optimise(&mut self, g: &Game, rng: &mut Rng, iters: usize, t0: f64, t1: f64) -> f64 {
        let n = self.p.len();
        let mut first = Vec::with_capacity(n + 1);
        let mut score = self.rollout_cache(g, &mut first);
        let mut best = (score, self.p.clone());
        for it in 0..iters {
            let frac = it as f64 / iters as f64;
            let temp = t0 * (t1 / t0).powf(frac);
            let amp = 1.0 - 0.9 * frac;
            let j = (rng.next() % n as u64) as usize;
            let old = self.p[j];
            let k = (rng.next() % NP as u64) as usize;
            self.p[j][k] = (self.p[j][k] + rng.range(-1.0, 1.0) * STEP[k] * amp).clamp(LO[k], HI[k]);
            if rng.next() % 3 == 0 {
                let k2 = (rng.next() % NP as u64) as usize;
                self.p[j][k2] = (self.p[j][k2] + rng.range(-1.0, 1.0) * STEP[k2] * amp).clamp(LO[k2], HI[k2]);
            }
            let thr = score - temp * rng.f().max(1e-300).ln();
            // p[j] is not used before the car targets checkpoint j-1
            let c = j.saturating_sub(1);
            let f = if c < first.len() { self.rollout_from(g, first[c], thr) } else { score };
            if f < thr {
                score = self.rollout_cache(g, &mut first);
                if score < best.0 {
                    best = (score, self.p.clone());
                }
            } else {
                self.p[j] = old;
            }
        }
        self.p = best.1;
        best.0
    }
}

impl Ctrl for SegPolicy {
    fn ctrl_act(&self, g: &Game, s: &State) -> Action {
        self.act(g, s)
    }
}
