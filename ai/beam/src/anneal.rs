//! Simulated annealing on the full action sequence with the exact objective
//! (finish turn + fraction of the last turn).
//!
//! The states along the current sequence are cached, so a mutation at step k
//! only re-simulates from k. When the sequence is exhausted before the end of
//! the race, the rollout controller finishes it (and those actions are kept).

use crate::search::{Policy, Rng};
use crate::sim::*;

pub struct Anneal<'a> {
    g: &'a Game,
    pol: Policy,
    pub actions: Vec<Action>,
    states: Vec<State>,
    pub score: f64,
}

impl<'a> Anneal<'a> {
    pub fn new(g: &'a Game, pol: Policy, actions: Vec<Action>) -> Anneal<'a> {
        let mut a = Anneal { g, pol, actions, states: vec![], score: 0.0 };
        let mut acts = std::mem::take(&mut a.actions);
        let (score, states) = a.run_full(&mut acts, 0, &[g.start]);
        a.actions = acts;
        a.states = states;
        a.score = score;
        a
    }

    /// Simulate `acts` from step k (states[..=k] are given). Extends `acts` with the
    /// controller when needed and truncates it at the finish.
    fn run_full(&self, acts: &mut Vec<Action>, k: usize, prefix: &[State]) -> (f64, Vec<State>) {
        let g = self.g;
        let mut states = prefix[..=k].to_vec();
        let mut s = states[k];
        let mut i = k;
        loop {
            if i >= MAX_TURN {
                return (10000.0 - 100.0 * s.cp as f64, states);
            }
            if i >= acts.len() {
                acts.push(self.pol.act(g, &s));
            }
            let t = g.step(&mut s, acts[i]);
            states.push(s);
            if s.cp == g.last {
                acts.truncate(i + 1);
                return (i as f64 + t.unwrap(), states);
            }
            i += 1;
        }
    }

    /// Fast evaluation of a candidate which differs from the current sequence from step k.
    #[inline]
    fn eval(&self, cand: &[Action], k: usize, limit: f64) -> f64 {
        let g = self.g;
        let mut s = self.states[k];
        let mut i = k;
        while i < MAX_TURN && (i as f64) <= limit {
            let a = if i < cand.len() { cand[i] } else { self.pol.act(g, &s) };
            let t = g.step(&mut s, a);
            if s.cp == g.last {
                return i as f64 + t.unwrap();
            }
            i += 1;
        }
        f64::INFINITY
    }

    fn mutate(&self, rng: &mut Rng, cand: &mut Vec<Action>) -> usize {
        let n = cand.len();
        let k = (rng.next() % n as u64) as usize;
        let r = rng.next() % 100;
        let small = |rng: &mut Rng| -> i32 {
            let d = 1 + (rng.next() % 3) as i32;
            if rng.next() & 1 == 0 { d } else { -d }
        };
        if r < 30 {
            // move some rotation from step k to a later step (heading preserved afterwards)
            let j = (k + 1 + (rng.next() % 6) as usize).min(n - 1);
            let d = small(rng);
            cand[k].angle = (cand[k].angle + d).clamp(-18, 18);
            cand[j].angle = (cand[j].angle - d).clamp(-18, 18);
        } else if r < 50 {
            cand[k].angle = (cand[k].angle + small(rng)).clamp(-18, 18);
        } else if r < 60 {
            cand[k].angle = (rng.next() % 37) as i32 - 18;
        } else if r < 75 {
            let d = small(rng) * (1 + (rng.next() % 20) as i32);
            cand[k].thrust = (cand[k].thrust + d).clamp(0, 200);
        } else if r < 85 {
            cand[k].thrust = if rng.next() & 1 == 0 { 200 } else { 0 };
        } else {
            // shift a block of rotations by one step
            let len = 2 + (rng.next() % 10) as usize;
            let end = (k + len).min(n - 1);
            if rng.next() & 1 == 0 {
                for i in k..end {
                    cand[i].angle = cand[i + 1].angle;
                }
            } else {
                for i in (k + 1..=end).rev() {
                    cand[i].angle = cand[i - 1].angle;
                }
            }
        }
        k
    }

    pub fn run(&mut self, rng: &mut Rng, iters: usize, t0: f64, t1: f64) {
        let mut cand = self.actions.clone();
        let mut best = (self.score, self.actions.clone());
        for it in 0..iters {
            let temp = t0 * (t1 / t0).powf(it as f64 / iters as f64);
            let k = self.mutate(rng, &mut cand);
            // accept if new < score - temp*ln(u)
            let thr = self.score - temp * rng.f().max(1e-300).ln();
            let f = self.eval(&cand, k, thr);
            if f < thr {
                let mut acts = std::mem::take(&mut cand);
                let (score, states) = self.run_full(&mut acts, k, &self.states);
                self.states = states;
                self.score = score;
                self.actions = acts;
                if score < best.0 {
                    best = (score, self.actions.clone());
                }
            }
            cand.clear();
            cand.extend_from_slice(&self.actions);
        }
        if best.0 < self.score {
            *self = Anneal::new(self.g, self.pol, best.1);
        }
    }
}
