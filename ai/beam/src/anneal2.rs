//! Simulated annealing where the genome is a list of target points + thrusts.
//!
//! Each turn the car rotates toward its target point (closed loop). A mutation at
//! step k shifts the trajectory, but the following targets pull it back toward the
//! previous path, so mutations stay local in effect.

use crate::search::{fast_atan2, Policy, Rng};
use crate::sim::*;

const RAD2DEG: f64 = 180.0 / std::f64::consts::PI;
const DEG2RAD: f64 = std::f64::consts::PI / 180.0;

#[derive(Clone, Copy, Debug)]
pub struct Gene {
    pub tx: f64,
    pub ty: f64,
    pub thrust: i32,
}

#[inline]
pub fn decode(s: &State, g: &Gene) -> Action {
    let desired = fast_atan2(g.ty - s.y as f64, g.tx - s.x as f64) * RAD2DEG;
    let mut diff = desired - s.angle as f64;
    while diff > 180.0 {
        diff -= 360.0;
    }
    while diff <= -180.0 {
        diff += 360.0;
    }
    Action { thrust: g.thrust, angle: ((diff + 0.5).floor() as i32).clamp(-18, 18) }
}

/// gene which reproduces action `a` from state `s` (target far along the new heading)
pub fn encode(s: &State, a: Action, dist: f64) -> Gene {
    let mut h = s.angle + a.angle.clamp(-18, 18);
    if h < 0 {
        h += 360;
    }
    let r = h as f64 * DEG2RAD;
    Gene { tx: s.x as f64 + r.cos() * dist, ty: s.y as f64 + r.sin() * dist, thrust: a.thrust }
}

pub struct Anneal2<'a> {
    g: &'a Game,
    pol: Policy,
    pub genes: Vec<Gene>,
    states: Vec<State>,
    pub actions: Vec<Action>,
    pub score: f64,
    pub dist: f64,
}

impl<'a> Anneal2<'a> {
    pub fn new(g: &'a Game, pol: Policy, actions: &[Action], dist: f64) -> Anneal2<'a> {
        let mut s = g.start;
        let mut genes = vec![];
        for a in actions {
            genes.push(encode(&s, *a, dist));
            g.step(&mut s, *a);
        }
        let mut me = Anneal2 { g, pol, genes, states: vec![g.start], actions: vec![], score: 0.0, dist };
        me.full(0);
        me
    }

    /// re-simulate the current genome from step k, extending it with the controller if needed
    fn full(&mut self, k: usize) {
        let g = self.g;
        self.states.truncate(k + 1);
        self.actions.truncate(k);
        let mut s = self.states[k];
        let mut i = k;
        loop {
            if i >= MAX_TURN {
                self.score = 10000.0 - 100.0 * s.cp as f64;
                return;
            }
            if i >= self.genes.len() {
                let a = self.pol.act(g, &s);
                self.genes.push(encode(&s, a, self.dist));
            }
            let a = decode(&s, &self.genes[i]);
            let t = g.step(&mut s, a);
            self.actions.push(a);
            self.states.push(s);
            if s.cp == g.last {
                self.genes.truncate(i + 1);
                self.score = i as f64 + t.unwrap();
                return;
            }
            i += 1;
        }
    }

    #[inline]
    fn eval(&self, cand: &[Gene], k: usize, limit: f64) -> f64 {
        let g = self.g;
        let mut s = self.states[k];
        let mut i = k;
        while i < MAX_TURN && (i as f64) <= limit {
            let a = if i < cand.len() { decode(&s, &cand[i]) } else { self.pol.act(g, &s) };
            let t = g.step(&mut s, a);
            if s.cp == g.last {
                return i as f64 + t.unwrap();
            }
            i += 1;
        }
        f64::INFINITY
    }

    fn gauss(rng: &mut Rng) -> f64 {
        let u = rng.f().max(1e-12);
        let v = rng.f();
        (-2.0 * u.ln()).sqrt() * (2.0 * std::f64::consts::PI * v).cos()
    }

    /// returns the first modified step
    fn mutate(&self, rng: &mut Rng, cand: &mut [Gene], sigma: f64) -> usize {
        let n = cand.len();
        let k = (rng.next() % n as u64) as usize;
        let r = rng.next() % 100;
        if r < 45 {
            let sc = sigma * (0.1 + 2.0 * rng.f());
            cand[k].tx += Self::gauss(rng) * sc;
            cand[k].ty += Self::gauss(rng) * sc;
        } else if r < 70 {
            let w = 2 + (rng.next() % 12) as usize;
            let end = (k + w).min(n);
            let sc = sigma * (0.1 + 2.0 * rng.f());
            let dx = Self::gauss(rng) * sc;
            let dy = Self::gauss(rng) * sc;
            for (j, gene) in cand[k..end].iter_mut().enumerate() {
                // triangular weight
                let wgt = 1.0 - ((j as f64 + 0.5) / (end - k) as f64 - 0.5).abs() * 2.0;
                gene.tx += dx * wgt;
                gene.ty += dy * wgt;
            }
        } else if r < 85 {
            let d = (1 + (rng.next() % 40) as i32) * if rng.next() & 1 == 0 { 1 } else { -1 };
            cand[k].thrust = (cand[k].thrust + d).clamp(0, 200);
        } else if r < 95 {
            cand[k].thrust = match rng.next() % 3 {
                0 => 0,
                1 => 200,
                _ => (rng.next() % 201) as i32,
            };
        } else {
            // re-aim the gene at the current position of a later state
            let j = (k + 1 + (rng.next() % 8) as usize).min(self.states.len() - 1);
            let s = self.states[j];
            cand[k].tx = s.x as f64 + s.vx as f64 * 2.0;
            cand[k].ty = s.y as f64 + s.vy as f64 * 2.0;
        }
        k
    }

    pub fn run(&mut self, rng: &mut Rng, iters: usize, t0: f64, t1: f64, sigma: f64) {
        let mut cand = self.genes.clone();
        let mut best = (self.score, self.genes.clone());
        for it in 0..iters {
            let frac = it as f64 / iters as f64;
            let temp = t0 * (t1 / t0).powf(frac);
            let sig = sigma * (1.0 - 0.8 * frac);
            let k = self.mutate(rng, &mut cand, sig);
            let thr = self.score - temp * rng.f().max(1e-300).ln();
            let f = self.eval(&cand, k, thr);
            if f < thr {
                std::mem::swap(&mut self.genes, &mut cand);
                self.full(k);
                if self.score < best.0 {
                    best = (self.score, self.genes.clone());
                }
            }
            cand.clear();
            cand.extend_from_slice(&self.genes);
        }
        if best.0 < self.score {
            self.genes = best.1;
            self.full(0);
        }
    }
}
