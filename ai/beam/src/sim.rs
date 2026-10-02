//! Bit-exact port of `game/` (pod.py, point.py, game.py).
//! Every floating point operation is written in the same order as the Python code
//! so that results match CPython (which uses the same C runtime math functions).

pub const MAX_TURN: usize = 600;
const R2: f64 = 360000.0;
const DEG2RAD: f64 = std::f64::consts::PI / 180.0;
const RAD2DEG: f64 = 180.0 / std::f64::consts::PI;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Action {
    pub thrust: i32,
    pub angle: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct State {
    pub x: i32,
    pub y: i32,
    pub vx: i32,
    pub vy: i32,
    pub angle: i32,
    pub cp: u16,
    pub turn: u16,
}

pub struct Game {
    /// checkpoints repeated 3 times + the fictive one (same as GameManager.checkpoints)
    pub cps: Vec<(f64, f64)>,
    /// id of the target checkpoint which ends the game
    pub last: u16,
    pub start: State,
    cos: [f64; 360],
    sin: [f64; 360],
}

fn py_round(x: f64) -> f64 {
    x.round_ties_even()
}

/// Python `x ** 0.5` (calls the CRT pow, not sqrt)
#[inline]
fn pow_half(x: f64) -> f64 {
    x.powf(0.5)
}

impl Game {
    pub fn from_test_in(test_in: &str) -> Game {
        let all: Vec<(f64, f64)> = test_in
            .split(';')
            .map(|s| {
                let mut it = s.trim().split(' ').map(|v| v.parse::<i64>().unwrap() as f64);
                (it.next().unwrap(), it.next().unwrap())
            })
            .collect();
        let mut rot: Vec<(f64, f64)> = all[1..].to_vec();
        rot.push(all[0]);
        let mut cps = Vec::new();
        for _ in 0..3 {
            cps.extend_from_slice(&rot);
        }
        let n2 = cps[cps.len() - 2];
        let n1 = cps[cps.len() - 1];
        let dist = pow_half((n2.0 - n1.0) * (n2.0 - n1.0) + (n2.1 - n1.1) * (n2.1 - n1.1));
        let factor = 50000.0 / dist;
        let lx = n1.0 * (factor + 1.0) - n2.0 * factor;
        let ly = n1.1 * (factor + 1.0) - n2.1 * factor;
        cps.push((py_round(lx), py_round(ly)));

        let start_pt = cps[cps.len() - 2];
        let p = cps[0];
        let d = pow_half((start_pt.0 - p.0) * (start_pt.0 - p.0) + (start_pt.1 - p.1) * (start_pt.1 - p.1));
        let dx = (p.0 - start_pt.0) / d;
        let dy = (p.1 - start_pt.1) / d;
        let a = dx.acos() * RAD2DEG;
        let a = if dy < 0.0 { 360.0 - a } else { a };
        let angle = py_round(a) as i32;

        let mut cos = [0.0; 360];
        let mut sin = [0.0; 360];
        for i in 0..360 {
            let r = i as f64 * DEG2RAD;
            cos[i] = r.cos();
            sin[i] = r.sin();
        }
        let last = (cps.len() - 1) as u16;
        Game {
            start: State { x: start_pt.0 as i32, y: start_pt.1 as i32, vx: 0, vy: 0, angle, cp: 0, turn: 0 },
            cps,
            last,
            cos,
            sin,
        }
    }

    pub fn from_json_file(path: &str) -> Game {
        let txt = std::fs::read_to_string(path).expect("cannot read testcase");
        let key = "\"testIn\":\"";
        let i = txt.find(key).expect("no testIn") + key.len();
        let j = txt[i..].find('"').unwrap() + i;
        Game::from_test_in(&txt[i..j])
    }

    /// Apply one action. Returns Some(t) when a checkpoint is crossed.
    #[inline]
    pub fn step(&self, s: &mut State, a: Action) -> Option<f64> {
        // rotate
        let mut angle = s.angle + a.angle.clamp(-18, 18);
        if angle >= 360 {
            angle -= 360;
        } else if angle < 0 {
            angle += 360;
        }
        s.angle = angle;
        // boost
        let th = a.thrust as f64;
        let vx = s.vx as f64 + self.cos[angle as usize] * th;
        let vy = s.vy as f64 + self.sin[angle as usize] * th;
        // checkpoint
        let t = self.collision(s.x as f64, s.y as f64, vx, vy, self.cps[s.cp as usize]);
        if t.is_some() {
            s.cp += 1;
        }
        // move + end
        // `as i32` truncates toward zero, like math.trunc
        s.x = (s.x as f64 + vx) as i32;
        s.y = (s.y as f64 + vy) as i32;
        s.vx = (vx * 0.85) as i32;
        s.vy = (vy * 0.85) as i32;
        s.turn += 1;
        t
    }

    #[inline]
    fn collision(&self, x: f64, y: f64, vx: f64, vy: f64, cp: (f64, f64)) -> Option<f64> {
        let nx = x + vx;
        let ny = y + vy;
        if x == nx && y == ny {
            return None;
        }
        // closest point on line (curr,next) from the checkpoint
        let da = ny - y;
        let db = x - nx;
        let c1 = da * x + db * y;
        let c2 = -db * cp.0 + da * cp.1;
        let det = da * da + db * db;
        let (px, py) = if det != 0.0 {
            ((da * c1 - db * c2) / det, (da * c2 + db * c1) / det)
        } else {
            (cp.0, cp.1)
        };
        let b_sq = (cp.0 - px) * (cp.0 - px) + (cp.1 - py) * (cp.1 - py);
        if b_sq > R2 {
            return None;
        }
        let s = (px - x) * vx + (py - y) * vy;
        if s < 0.0 {
            return None;
        }
        let a_sq = (x - px) * (x - px) + (y - py) * (y - py);
        let f = (R2 - b_sq).sqrt();
        let t = (a_sq.sqrt() - f) / pow_half(vx * vx + vy * vy);
        if t < 0.0 || t > 1.0 {
            return None;
        }
        Some(t)
    }

    /// Score of a full sequence as computed by train.get_score (1000 if unfinished)
    pub fn score(&self, actions: &[Action]) -> f64 {
        let mut s = self.start;
        for (i, a) in actions.iter().enumerate() {
            let t = self.step(&mut s, *a);
            if s.cp == self.last {
                return i as f64 + t.unwrap();
            }
            if s.turn as usize == MAX_TURN {
                break;
            }
        }
        1000.0
    }
}

pub fn parse_actions(s: &str) -> Vec<Action> {
    s.trim()
        .split(';')
        .filter(|x| !x.is_empty())
        .map(|p| {
            let mut it = p.split(',').map(|v| v.trim().parse::<i32>().unwrap());
            Action { thrust: it.next().unwrap(), angle: it.next().unwrap() }
        })
        .collect()
}

pub fn format_actions(a: &[Action]) -> String {
    a.iter().map(|a| format!("{},{}", a.thrust, a.angle)).collect::<Vec<_>>().join(";")
}
