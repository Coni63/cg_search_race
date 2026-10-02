//! Genetic algorithm on complete paths.
//!
//! Paths are encoded as target-point genes (see anneal2), which are closed loop:
//! a suffix taken from another path still drives the car along that path even if
//! the state at the junction differs slightly. Crossover = prefix of A up to its
//! crossing of checkpoint j + suffix of B from its crossing of the same checkpoint.
//! Children are then polished by the target-point SA.

use crate::anneal2::{decode, encode, Anneal2, Gene};
use crate::search::{Policy, Rng};
use crate::sim::*;

struct Indiv {
    genes: Vec<Gene>,
    score: f64,
    /// turn index at which each checkpoint was crossed
    cross: Vec<usize>,
}

fn evaluate(g: &Game, genes: &[Gene]) -> Option<Indiv> {
    let mut s = g.start;
    let mut cross = vec![];
    for (i, gene) in genes.iter().enumerate() {
        let a = decode(&s, gene);
        let t = g.step(&mut s, a);
        if let Some(t) = t {
            cross.push(i + 1);
            if s.cp == g.last {
                return Some(Indiv { genes: genes[..=i].to_vec(), score: i as f64 + t, cross });
            }
        }
    }
    None
}

fn from_actions(g: &Game, actions: &[Action], dist: f64) -> Option<Indiv> {
    let mut s = g.start;
    let mut genes = vec![];
    for a in actions {
        genes.push(encode(&s, *a, dist));
        g.step(&mut s, *a);
    }
    evaluate(g, &genes)
}

pub struct SpliceParams {
    pub pop: usize,
    pub gens: usize,
    pub sa_iters: usize,
    pub sigma: f64,
    pub t0: f64,
    pub dist: f64,
}

pub fn run(g: &Game, pol: Policy, inits: &[Vec<Action>], sp: &SpliceParams, rng: &mut Rng, log: &str) -> (f64, Vec<Action>) {
    let mut pop: Vec<Indiv> = inits.iter().filter_map(|a| from_actions(g, a, sp.dist)).collect();
    pop.sort_by(|a, b| a.score.partial_cmp(&b.score).unwrap());
    pop.dedup_by(|a, b| (a.score - b.score).abs() < 1e-9);
    pop.truncate(sp.pop);
    eprintln!("{log}: splice pop {} best {:.3}", pop.len(), pop[0].score);

    for gen in 0..sp.gens {
        // all crossovers between pairs of the population at every checkpoint
        let mut children: Vec<Indiv> = vec![];
        for a in 0..pop.len() {
            for b in 0..pop.len() {
                if a == b {
                    continue;
                }
                let (pa, pb) = (&pop[a], &pop[b]);
                for j in 0..pa.cross.len().min(pb.cross.len()) {
                    let mut genes = pa.genes[..pa.cross[j]].to_vec();
                    genes.extend_from_slice(&pb.genes[pb.cross[j]..]);
                    if let Some(c) = evaluate(g, &genes) {
                        if c.score < pa.score.min(pb.score) - 1e-9 {
                            children.push(c);
                        }
                    }
                }
            }
        }
        children.sort_by(|a, b| a.score.partial_cmp(&b.score).unwrap());
        children.dedup_by(|a, b| (a.score - b.score).abs() < 1e-9);
        children.truncate(sp.pop / 2 + 1);

        // polish the best children with the SA, then merge into the population
        for (k, c) in children.iter_mut().enumerate() {
            if sp.sa_iters == 0 || k >= 3 {
                break;
            }
            let acts: Vec<Action> = {
                let mut s = g.start;
                c.genes.iter().map(|gene| {
                    let a = decode(&s, gene);
                    g.step(&mut s, a);
                    a
                }).collect()
            };
            let mut sa = Anneal2::new(g, pol, &acts, sp.dist);
            sa.run(rng, sp.sa_iters, sp.t0, 0.005, sp.sigma);
            if let Some(better) = evaluate(g, &sa.genes) {
                if better.score < c.score {
                    *c = better;
                }
            }
        }
        let n_children = children.len();
        pop.extend(children);
        pop.sort_by(|a, b| a.score.partial_cmp(&b.score).unwrap());
        pop.dedup_by(|a, b| (a.score - b.score).abs() < 1e-9);
        pop.truncate(sp.pop);
        eprintln!("{log}: splice gen {gen}: {n_children} children, best {:.3}", pop[0].score);
        if n_children == 0 {
            break;
        }
    }

    let best = &pop[0];
    let mut s = g.start;
    let acts: Vec<Action> = best.genes.iter().map(|gene| {
        let a = decode(&s, gene);
        g.step(&mut s, a);
        a
    }).collect();
    (g.score(&acts), acts)
}
