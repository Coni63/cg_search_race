mod anneal;
mod anneal2;
mod search;
mod segpol;
mod splice;
mod sim;

use anneal::Anneal;
use anneal2::Anneal2;
use search::*;
use segpol::SegPolicy;
use sim::*;
use std::io::BufRead;
use std::sync::{Arc, Mutex};

fn arg<T: std::str::FromStr>(args: &[String], name: &str, default: T) -> T {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}

fn read_stdin_pairs() -> Vec<(String, String)> {
    std::io::stdin()
        .lock()
        .lines()
        .map(|l| l.unwrap())
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let mut it = l.splitn(2, '\t');
            (it.next().unwrap().to_string(), it.next().unwrap_or("").to_string())
        })
        .collect()
}

fn solve(file: &str, init: &str, args: &[String]) -> (f64, Vec<Action>) {
    let width: usize = arg(args, "--width", 100);
    let iters: usize = arg(args, "--iters", 1);
    let seed: u64 = arg(args, "--seed", 1);
    let n_pol: usize = arg(args, "--policies", 4);
    let step: usize = arg(args, "--astep", 1);
    let noise: f64 = arg(args, "--noise", 0.0);

    let g = Game::from_json_file(file);
    let mut rng = Rng::new(seed ^ (file.len() as u64 * 7919));
    let pols = tune_policies(&g, &mut rng, 3000, n_pol);
    let policies: Vec<Policy> = pols.iter().map(|p| p.1).collect();

    let init_actions = parse_actions(init);
    let mut inc = if init_actions.is_empty() {
        Incumbent::new(&g, policies[0].rollout_actions(&g, &g.start))
    } else {
        Incumbent::new(&g, init_actions)
    };
    let start_score = inc.score;
    eprintln!("{file}: init {start_score:.3} best policy {:.3}", pols[0].0);

    let mut angles: Vec<i32> = (-18..=18).step_by(step).collect();
    if !angles.contains(&18) {
        angles.push(18);
    }
    let sa_iters: usize = arg(args, "--sa", 0);
    let rounds: usize = arg(args, "--rounds", 1);
    let t0: f64 = arg(args, "--t0", 0.5);
    let t1: f64 = arg(args, "--t1", 0.005);
    let mut sa = Anneal::new(&g, policies[0], inc.actions.clone());
    for r in 0..rounds {
        if sa_iters == 0 {
            break;
        }
        sa.run(&mut rng, sa_iters, t0, t1);
        eprintln!("{file}: sa round {r} -> {:.3}", sa.score);
    }
    if sa.score < inc.score {
        inc = Incumbent::new(&g, sa.actions.clone());
    }

    let seg_iters: usize = arg(args, "--seg", 0);
    let seg_rounds: usize = arg(args, "--segrounds", 1);
    let seg_t0: f64 = arg(args, "--segt0", 0.5);
    let mut segs: Vec<(f64, SegPolicy)> = vec![];
    if seg_iters > 0 {
        let mut best_seg = f64::INFINITY;
        for r in 0..seg_rounds {
            let p0 = &policies[r % policies.len()];
            let mut sp = SegPolicy::uniform(&g, p0.kv, p0.ksw, p0.rsw, p0.cut, p0.low as f64);
            for j in 0..sp.p.len() {
                if j + 1 < g.last as usize {
                    let (c, n) = (g.cps[j], g.cps[j + 1]);
                    let d = ((n.0 - c.0).powi(2) + (n.1 - c.1).powi(2)).sqrt();
                    sp.p[j][0] = (n.0 - c.0) / d * p0.off;
                    sp.p[j][1] = (n.1 - c.1) / d * p0.off;
                }
            }
            let f = sp.optimise(&g, &mut rng, seg_iters, seg_t0, 0.01);
            best_seg = best_seg.min(f);
            eprintln!("{file}: seg round {r} -> {f:.3}");
            if f < inc.score {
                inc = Incumbent::new(&g, sp.actions(&g));
            }
            segs.push((f, sp));
        }
        segs.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        eprintln!("{file}: seg best {best_seg:.3}");
    }

    for it in 0..iters {
        if width == 0 { break; }
        let bp = BeamParams { width, angles: angles.clone(), thrusts: vec![0, 200], noise };
        let mut ctrls: Vec<&dyn Ctrl> = segs.iter().map(|s| &s.1 as &dyn Ctrl).collect();
        if ctrls.is_empty() {
            ctrls = policies.iter().map(|p| p as &dyn Ctrl).collect();
        }
        beam(&g, &ctrls, &mut inc, &bp, &mut rng);
        eprintln!("{file}: iter {it} -> {:.3}", inc.score);
    }


    let sa2_iters: usize = arg(args, "--sa2", 0);
    let rounds2: usize = arg(args, "--rounds2", 1);
    let sigma: f64 = arg(args, "--sigma", 300.0);
    let dist: f64 = arg(args, "--dist", 3000.0);
    let t0b: f64 = arg(args, "--t0b", 0.3);
    if sa2_iters > 0 {
        let mut sa2 = Anneal2::new(&g, policies[0], &inc.actions, dist);
        eprintln!("{file}: sa2 encoded {:.3}", sa2.score);
        for r in 0..rounds2 {
            sa2.run(&mut rng, sa2_iters, t0b, t1, sigma);
            eprintln!("{file}: sa2 round {r} -> {:.3}", sa2.score);
            if sa2.score < inc.score {
                inc = Incumbent::new(&g, sa2.actions.clone());
            }
        }
    }
    (inc.score, inc.actions)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        // stdin: "testfile<TAB>actions" -> stdout: "testfile<TAB>score"
        Some("replay") => {
            for (file, actions) in read_stdin_pairs() {
                let g = Game::from_json_file(&file);
                println!("{}\t{:?}", file, g.score(&parse_actions(&actions)));
            }
        }
        // stdin: "testfile<TAB>initial actions (may be empty)" -> stdout: "testfile<TAB>score<TAB>actions"
        Some("solve") => {
            let jobs = Arc::new(Mutex::new(read_stdin_pairs()));
            let threads: usize = arg(&args, "--threads", 12);
            let out = Arc::new(Mutex::new(()));
            std::thread::scope(|sc| {
                for _ in 0..threads {
                    let jobs = jobs.clone();
                    let out = out.clone();
                    let args = &args;
                    sc.spawn(move || loop {
                        let job = jobs.lock().unwrap().pop();
                        let Some((file, init)) = job else { break };
                        let (score, actions) = solve(&file, &init, args);
                        let _l = out.lock().unwrap();
                        println!("{}\t{:?}\t{}", file, score, format_actions(&actions));
                    });
                }
            });
        }
        // stdin: several "testfile<TAB>actions" lines per testcase -> GA by path splicing
        Some("splice") => {
            let mut groups: Vec<(String, Vec<Vec<Action>>)> = vec![];
            for (file, actions) in read_stdin_pairs() {
                let acts = parse_actions(&actions);
                match groups.iter_mut().find(|g| g.0 == file) {
                    Some(g) => g.1.push(acts),
                    None => groups.push((file, vec![acts])),
                }
            }
            let jobs = Arc::new(Mutex::new(groups));
            let threads: usize = arg(&args, "--threads", 12);
            let sp = splice::SpliceParams {
                pop: arg(&args, "--pop", 30),
                gens: arg(&args, "--gens", 10),
                sa_iters: arg(&args, "--sa2", 1000000),
                sigma: arg(&args, "--sigma", 1000.0),
                t0: arg(&args, "--t0b", 0.3),
                dist: arg(&args, "--dist", 3000.0),
            };
            let seed: u64 = arg(&args, "--seed", 1);
            let out = Arc::new(Mutex::new(()));
            std::thread::scope(|sc| {
                for _ in 0..threads {
                    let jobs = jobs.clone();
                    let out = out.clone();
                    let sp = &sp;
                    sc.spawn(move || loop {
                        let job = jobs.lock().unwrap().pop();
                        let Some((file, inits)) = job else { break };
                        let g = Game::from_json_file(&file);
                        let mut rng = Rng::new(seed ^ (file.len() as u64 * 7919));
                        let pol = tune_policies(&g, &mut rng, 1000, 1)[0].1;
                        let (score, actions) = splice::run(&g, pol, &inits, sp, &mut rng, &file);
                        let _l = out.lock().unwrap();
                        println!("{}	{:?}	{}", file, score, format_actions(&actions));
                    });
                }
            });
        }
        Some("wide") => {
            let g = Game::from_json_file(&args[2]);
            let width: usize = arg(&args, "--width", 10000);
            let step: usize = arg(&args, "--astep", 3);
            let wv: f64 = arg(&args, "--wv", 0.0);
            let mut angles: Vec<i32> = (-18..=18).step_by(step).collect();
            if !angles.contains(&18) { angles.push(18); }
            let t = std::time::Instant::now();
            let (f, acts) = wide_beam(&g, width, &angles, &[0, 100, 200], wv);
            eprintln!("width {width} wv {wv}: {f:.3} in {:.1}s", t.elapsed().as_secs_f64());
            println!("{}	{:?}	{}", args[2], f, format_actions(&acts));
        }
        Some("bench") => {
            let g = Game::from_json_file(&args[2]);
            let mut rng = Rng::new(1);
            let p = Policy::random(&mut rng);
            let t = std::time::Instant::now();
            let mut steps = 0u64;
            let mut s = g.start;
            for _ in 0..2_000_000 {
                let a = p.act(&g, &s);
                g.step(&mut s, a);
                steps += 1;
                if s.cp == g.last || s.turn as usize >= MAX_TURN { s = g.start; }
            }
            eprintln!("policy steps: {:.1} ns/step", t.elapsed().as_nanos() as f64 / steps as f64);
            let t = std::time::Instant::now();
            let mut s = g.start;
            for i in 0..2_000_000u64 {
                g.step(&mut s, Action { thrust: 200, angle: (i % 37) as i32 - 18 });
                if s.cp == g.last || s.turn as usize >= MAX_TURN { s = g.start; }
            }
            eprintln!("raw steps: {:.1} ns/step {:?}", t.elapsed().as_nanos() as f64 / 2e6, s);
        }
        _ => eprintln!("usage: beam replay|solve [--width N --iters N --seed N --threads N] < lines"),
    }
}
