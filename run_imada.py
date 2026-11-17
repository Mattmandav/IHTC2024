"""
Run the SDU-IMADA IHTC-2024 solver on every instance used by run_instances.py,
one replication per call, recording:
  - the first feasible solution each of its four search threads reaches,
  - how many moves (iterations) are evaluated, and how many improve,
  - the final solution, checked with our validator.

The solver is their code with counting added (imada_solver/). Build it once
on the login node before submitting:
    bash imada_solver/build.sh

On STORM, imada_slurm.sh runs this as a job array: array task R runs
replication R with seed R, as run_instances.py does for our methods.

By hand, from the repo root:
    uv run run_imada.py 3              run replication 3
    uv run run_imada.py 3 --dry-run    list its jobs

Output, per replication (next to our methods' results):
    data/solutions/4core/imada/rep<RR>/sol_<instance>.json     solution
    data/solutions/4core/imada/rep<RR>/stats_<instance>.json   per-thread counts
    data/solutions/4core/imada/rep<RR>/result_<instance>.json  summary
A job whose result file exists is skipped, so a resubmitted task resumes.

Notes on comparing with our framework:
  - IMADA's run time is fixed in its code: 595 s of search per run.
  - It always runs four searches in parallel threads, so it needs 4 cores.
  - Its "iteration" is one delta-evaluated move; ours is one candidate solution
    checked by the validator. The counts measure the same idea at very
    different granularity, so compare them with care.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

from run_instances import INSTANCE_FOLDER, INSTANCE_SETS, SOLUTION_FOLDER, VALIDATOR

SOLVER = "imada_solver/build/imada_solver"
COMMIT_FILE = "imada_solver/build/imada_commit.txt"
CORES = 4  # the solver always runs four threads
TIMEOUT = 900  # seconds; the solver itself stops after about 600


def cpu_model():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def validate(instance_path, solution_path):
    out = subprocess.run(
        [VALIDATOR, instance_path, solution_path], capture_output=True, text=True
    ).stdout
    violations = cost = None
    for line in out.splitlines():
        if line.startswith("Total violations"):
            violations = int(line.split()[-1])
        elif line.startswith("Total cost"):
            cost = int(line.split()[-1])
    return violations, cost


def write_json(path, data):
    """Atomic write, so an interrupted job never leaves a half-written file."""
    with tempfile.NamedTemporaryFile(
        "w", dir=os.path.dirname(path), suffix=".tmp", delete=False
    ) as f:
        json.dump(data, f, indent=2)
    os.replace(f.name, path)


def summarise(stats):
    threads = stats["threads"]
    feasible = [t for t in threads if t["feasible_found"]]
    first = min(feasible, key=lambda t: t["feasible_seconds"]) if feasible else None
    total = lambda key: sum(t[key] for t in threads)
    return {
        # First feasible solution: the thread that got there earliest
        "first_feasible_seconds": first["feasible_seconds"] if first else None,
        "first_feasible_cost": first["feasible_soft"] if first else None,
        "first_feasible_thread": first["thread"] if first else None,
        "threads_reaching_feasibility": len(feasible),
        # Moves evaluated and improving moves, summed over the four threads
        "iterations": total("sa_iterations") + total("ls_iterations"),
        "improving_iterations": total("sa_improving") + total("ls_improving"),
        "new_best_solutions": total("sa_new_best") + total("ils_new_best"),
        "sa_iterations": total("sa_iterations"),
        "sa_improving": total("sa_improving"),
        "ls_iterations": total("ls_iterations"),
        "ls_improving": total("ls_improving"),
        "ils_cycles": total("ils_iterations"),
        "best_thread": stats["best_thread"],
        "solver_cost": threads[stats["best_thread"] - 1]["final_soft"],
        "solver_seconds": stats["total_seconds"],
    }


def run_job(instance, rep, folder, commit, cpu):
    os.makedirs(folder, exist_ok=True)
    instance_path = os.path.join(INSTANCE_FOLDER, instance + ".json")
    solution_path = os.path.join(folder, "sol_{}.json".format(instance))
    stats_path = os.path.join(folder, "stats_{}.json".format(instance))
    result_path = os.path.join(folder, "result_{}.json".format(instance))
    seed = rep

    start = time.time()
    try:
        subprocess.run(
            [SOLVER, instance_path, str(seed), solution_path, "0", stats_path],
            capture_output=True, text=True, check=True, timeout=TIMEOUT,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print("  FAILED: {}".format(e), flush=True)
        return None
    elapsed = time.time() - start

    violations, cost = validate(instance_path, solution_path)
    with open(stats_path) as f:
        stats = json.load(f)

    # Written last: its presence marks the job as done
    write_json(result_path, {
        "instance": instance,
        "method": "imada",
        "replication": rep,
        "seed": seed,
        "cost": cost,
        "violations": violations,
        "feasible": violations == 0,
        **summarise(stats),
        "cores": CORES,
        "wall_seconds": elapsed,
        "host": os.uname().nodename,
        "cpu": cpu,
        "imada_commit": commit,
    })
    return cost, violations


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "replication", nargs="?", type=int,
        help="replication number (default: the SLURM array task ID)",
    )
    parser.add_argument("--dry-run", action="store_true", help="list the jobs and stop")
    args = parser.parse_args()

    rep = args.replication
    if rep is None:
        if "SLURM_ARRAY_TASK_ID" not in os.environ:
            parser.error("give a replication number, or run inside a SLURM array")
        rep = int(os.environ["SLURM_ARRAY_TASK_ID"])
    if rep < 1:
        parser.error("replications are numbered from 1")

    allocated = int(os.environ.get("SLURM_CPUS_PER_TASK", CORES))
    if allocated != CORES:
        sys.exit("The IMADA solver runs {} threads; submit with -c {} (got {}).".format(
            CORES, CORES, allocated))

    # Fail early on anything missing, before hours of runs
    instances = [i for names, _ in INSTANCE_SETS.values() for i in names]
    missing = [i for i in instances if not os.path.isfile(os.path.join(INSTANCE_FOLDER, i + ".json"))]
    if missing:
        sys.exit("Missing from {}: {}".format(INSTANCE_FOLDER, " ".join(missing)))
    if not os.path.isfile(VALIDATOR):
        sys.exit("Validator not found at {}. Compile it first.".format(VALIDATOR))
    if not os.path.isfile(SOLVER):
        sys.exit("IMADA solver not built. Run: bash imada_solver/build.sh")
    commit = open(COMMIT_FILE).read().strip() if os.path.isfile(COMMIT_FILE) else None
    cpu = cpu_model()

    folder = os.path.join(SOLUTION_FOLDER, "{}core".format(CORES), "imada", "rep{:02d}".format(rep))
    jobs = [
        i for i in instances
        if not os.path.isfile(os.path.join(folder, "result_{}.json".format(i)))
    ]
    print("IMADA replication {} (seed {}): {} instances to run, about {:.1f} h".format(
        rep, rep, len(jobs), len(jobs) * 600 / 3600))

    for n, instance in enumerate(jobs, start=1):
        if args.dry_run:
            print("  " + instance)
            continue
        print("[{}/{}] {}".format(n, len(jobs), instance), flush=True)
        outcome = run_job(instance, rep, folder, commit, cpu)
        if outcome:
            print("  cost {} violations {}".format(*outcome), flush=True)
