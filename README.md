# Car Racing - Optimization Puzzle

An optimization puzzle where you control a car racing through a series of checkpoints as fast as possible.

---

## 🎯 The Goal

Finish racing through a series of checkpoints in as few turns as possible.

---

## 📜 Rules

### General Mechanics
* **Map Dimensions:** $16000 \times 9000$ units. Top-left corner is $(X=0, Y=0)$.
* **Targeting:** Target checkpoint is indicated by `checkpointIndex`, pointing to a value in the checkpoints provided during initialization.
* **Repetition:** Checkpoints are repeated in the initial input (unlike CSB).

### Checkpoints
* Circular shape with a **radius of 600 units**.
* Layout is determined by test cases.
* No checkpoints overlap.
* To validate a checkpoint, the **center of the car** must be within **600 units** of the checkpoint center.

### Car Control
* Every turn, you issue a command containing a target position `(X, Y)` and a `THRUST` value.
* **Max Turn Angle:** $18^\circ$ per turn from the current heading.
* Once the heading is updated, the car applies the given thrust to move in the new direction.

### Win / Lose Conditions
* **Win:** Visit all checkpoints in the provided order before time runs out.
* **Lose:**
  * Exceed 600 rounds.
  * Provide an invalid output/action.

---

## 🤓 Expert Rules

### Movement Physics
On each turn, car movement is calculated in the following sequence:

1. **Rotation:** The car rotates toward the target point (maximum $18^\circ$ rotation).
2. **Acceleration:** The car's facing unit vector is multiplied by `THRUST`. The resulting vector is added to the current speed vector $(v_x, v_y)$.
3. **Position Update:** The current speed vector is added to the car's position $(x, y)$.
4. **Friction / Deceleration:** The speed vector is multiplied by $0.85$.
5. **Rounding:** Speed values are truncated, angles are converted to degrees and rounded, and position values are truncated.

### Angles & Orientations
* Angles are given in **degrees** relative to the positive X-axis:
  * $0^\circ \rightarrow (1, 0)$ (East)
  * $90^\circ \rightarrow$ South
  * $180^\circ \rightarrow$ West
  * $270^\circ \rightarrow$ North

---

## 📥 Game Input & Output

### Initialization Input

The program first reads standard input for map setups:

* **Line 1:** `checkpoints` (Integer) — Total count of checkpoints to pass (repeated 3 times for convenience).
* **Next `checkpoints` lines:** Two integers `checkpointX checkpointY` representing the coordinates of each checkpoint.

---

### Turn Input

Each game turn provides **one line with 6 integers**:

$$\text{checkpointIndex} \quad x \quad y \quad v_x \quad v_y \quad \text{angle}$$

* **`checkpointIndex`**: Index of the next checkpoint to reach.
* **`x`, `y`**: Current position of the car.
* **`vx`, `vy`**: Current speed vector.
* **`angle`**: Heading angle in degrees ($0^\circ$ to $360^\circ$).

---

### Turn Output

Standard output format:

```text
X Y THRUST [message]
```

* **`X`, `Y`**: Coordinates to aim at.
* **`THRUST`**: Thrust integer value.
* **`message`** *(Optional)*: Message displayed above the car.

#### Alternative Output Format
```text
EXPERT rotationAngle thrust [message]
```

#### Optional Debugging Information
If the message is set to `debug` once, the game summary will include extra information (e.g., referee collision time from the previous round).

---

## ⚙️ Constraints

| Parameter | Constraint |
| :--- | :--- |
| **Checkpoints** | $9 \le \text{checkpoints} \le 24$ |
| **Thrust** | $0 \le \text{thrust} \le 200$ |
| **Angle** | $0^\circ \le \text{angle} \le 360^\circ$ |
| **First Turn Response Time** | $\le 1000 \text{ ms}$ |
| **Turn Response Time** | $\le 50 \text{ ms}$ |


## Run locally -- Developer only

### Clone the repository

```sh
git clone https://github.com/Coni63/cg_search_race.git
cd cg_search_race
```

### Install the environment

```sh
python -m venv venv
venv/Scripts/activate.ps1
pip install -r requirements.txt
```

```sh
cd api
mkvirtualenv venv --python=/usr/bin/python3.10
workon venv
pip install -r requirements.txt
```

### Run

The idea is to run as many optimisations as possible per track and save every result in a DB (`ai/AG/results.db`) to get the best simulations for every track. On CG, the sequence will be taken based on a hash of the input checkpoints.

#### Python GA (original agent)

```sh
make train      # poetry run python train.py
```

#### Rust optimiser (`ai/beam`, recommended)

A bit-exact port of `game/` in Rust (~1000x faster), requires `cargo`. It starts from the best sequence stored in the DB for each testcase, tries to improve it, checks every result with the Python engine and saves improvements in the DB (`generation = -1`).

```sh
cargo build --release --manifest-path ai/beam/Cargo.toml
python -m ai.beam.run --seed 3 --width 0 --seg 8000000 --segrounds 3 --sa2 6000000 --sigma 1000 --threads 12
```

Change `--seed` at each pass to explore new trajectories (a pass takes ~45 min on 12 threads).

Main options (see `ai/beam/src/main.rs`):

| Option | Description |
| :--- | :--- |
| `--seg N` / `--segrounds R` | SA on a closed-loop controller with one set of parameters per checkpoint (N iterations, R restarts). Finds new trajectories: the main source of gains. |
| `--sa2 N` / `--sigma S` / `--t0b T` | SA on the sequence encoded as target points (polish of the best path). |
| `--width W` | Beam search guided by rollouts (`0` to disable). |
| `--seed N` | Random seed. |
| `--threads N` | Number of testcases solved in parallel. |
| `--splice` | GA on all the paths stored for each testcase (crossover by splicing at checkpoints), e.g. `--splice --pop 30 --gens 10 --sa2 1000000`. |

#### Export the solutions

```sh
make evaluate   # writes output/sols.txt (hash of the track -> actions)
```

### Run tests / coverage

You can run tests / coverage simply by running the following commands:

```sh
venv/Scripts/activate.ps1  # or source venv/bin/activate or workon venv
coverage run -m unittest discover
```

If you want to go further, here is some usefull commands to use

```sh
coverage xml  # create the cobertura coverage.xml file -- do not commit it
coverage json # same file but in json -- do not commit it
coverage html # generate a htmlcov folder with coverage result as HTML file -- do not commit it
coverage report # get report in the console

python -m unittest discover # run only unittest and don't evaluate coverage
python -m unittest test_module1 test_module2  # run only some modules
python -m unittest test_module.TestClass      # run only one class in a module
python -m unittest test_module.TestClass.test_method # run only 1 test in a class
```

### Freeze the environment

In case you install a new dependency, don't forget to update the requirements.txt 😉

```sh
cd api
venv/Scripts/activate.ps1  # or source venv/bin/activate or workon venv
pip freeze > requirements.txt
```