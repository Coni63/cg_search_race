"""
Run the Rust optimiser (ai/beam) on every testcase, starting from the best sequence stored in the DB,
and save the improved sequences in the DB.

Usage (from the project root):
    cargo build --release --manifest-path ai/beam/Cargo.toml
    python -m ai.beam.run --seg 10000000 --sa2 6000000 --sigma 1000
Any argument is forwarded to the solver (see ai/beam/src/main.rs).
With --splice, every stored path of a testcase is used as the initial population of a GA
(path splicing crossover + target-point SA):
    python -m ai.beam.run --splice --pop 30 --gens 10 --sa2 1000000
"""
import glob
import os
import subprocess
import sys

from ai.AG import Saver
from ai.AG.eval import Eval
from train import get_score

EXE = os.path.abspath("ai/beam/target/release/beam.exe" if os.name == "nt" else "ai/beam/target/release/beam")
TAG = -1  # value stored in the `generation` column to recognise these runs


def main(solver_args: list[str], pattern="testcases/test*.json"):
    saver = Saver("ai/AG/results.db")
    files = sorted(f.replace("\\", "/") for f in glob.glob(pattern))
    before = {}
    lines = []
    for f in files:
        best = saver.get_best(os.path.basename(f))
        actions, score = best if best else ("", 1000)
        before[f] = score
        lines.append(f"{f}\t{actions}\n")

    mode = "solve"
    if "--splice" in solver_args:
        # GA mode: feed every stored path of each testcase
        solver_args = [a for a in solver_args if a != "--splice"]
        mode = "splice"
        lines = []
        for f in files:
            rows = saver.cur.execute(
                "SELECT actions FROM experiences WHERE testfile LIKE ? ORDER BY score ASC LIMIT 60",
                (f"%{os.path.basename(f)}",),
            ).fetchall()
            lines += [f"{f}\t{r[0]}\n" for r in rows]

    proc = subprocess.Popen(
        [EXE, mode, *solver_args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    proc.stdin.write("".join(lines))
    proc.stdin.close()

    total_before = total_after = 0
    for line in proc.stdout:
        f, score, actions = line.rstrip("\n").split("\t")
        # double check with the reference Python engine before saving
        py_score = get_score(f, Eval.from_str(actions).moves)
        assert abs(py_score - float(score)) < 1e-9, (f, py_score, score)
        gain = before[f] - py_score
        print(f"{f}: {before[f]:.3f} -> {py_score:.3f} ({gain:+.3f})", flush=True)
        if gain > 1e-9:
            saver.save(f, 0, 0, TAG, actions, py_score)
        total_before += before[f]
        total_after += min(py_score, before[f])
    proc.wait()
    print(f"total {total_before:.3f} -> {total_after:.3f}")


if __name__ == "__main__":
    main(sys.argv[1:])
