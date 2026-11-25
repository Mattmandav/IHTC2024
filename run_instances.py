"""
Results for every instance (public, hidden and supplementary) and every
selection/acceptance configuration, using our heuristics and the tuned
parameters in irace_results/. One call runs one replication.

On STORM, instances_slurm.sh runs it as a job array: array task R runs
replication R with seed R, so the array size sets the number of replications.

By hand, from the repo root:
    uv run run_instances.py 3              run replication 3
    uv run run_instances.py 3 --dry-run    list its jobs and estimated hours

Output, per configuration and replication:
    data/solutions/<cores>core/<method>/rep<RR>/sol_<instance>.json
    data/solutions/<cores>core/<method>/rep<RR>/result_<instance>.json
The result file holds the cost, feasibility, seed, parameters and the initial
solution generation cycles. Nothing is overwritten: a job whose result file
exists is skipped, so a resubmitted task carries on where it stopped.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time

from src.optimise.optimiser import main

INSTANCE_FOLDER = "data/instances"
SOLUTION_FOLDER = "data/solutions"
IRACE_FOLDER = "irace_results"
GREEDY_FOLDER = "data/greedy_cycles"
VALIDATOR = "./bin/IHTP_Validator"
HEURISTIC_SET = "ours"
TIME_TOLERANCE = 3

# Instance sets and run time per instance (seconds). Supplementary was run
# for 7200 s in the paper; here every set uses 600 s.
INSTANCE_SETS = {
    "public": (["i{:02d}".format(n) for n in range(1, 31)], 600),
    "hidden": (["m{:02d}".format(n) for n in range(1, 31)], 600),
    "supplementary": (
        ["l{}_{}".format(h, i) for h in (35, 42, 49, 56) for i in range(1, 7)]
        + ["small{:02d}".format(i) for i in range(1, 10)],
        600,
    ),
}

SELECTIONS = {"random": "r", "qlearner": "QL", "mcrl": "mcrl"}
ACCEPTANCES = {"sa": "sa", "r2r": "r2r", "improve_only": "io"}


def method_id(selection, acceptance):
    """Same naming as run_irace.py, e.g. QL_sa_ours."""
    return "{}_{}_{}".format(SELECTIONS[selection], ACCEPTANCES[acceptance], HEURISTIC_SET)


def tuned_params(selection, acceptance):
    """Best configuration found by irace: the first row of its CSV."""
    path = os.path.join(IRACE_FOLDER, method_id(selection, acceptance) + ".csv")
    if not os.path.isfile(path):
        sys.exit("No tuned parameters at {}".format(path))
    with open(path) as f:
        best = next(csv.DictReader(f))
    params = {"sequence_length": int(float(best["sequence_length"]))}
    for key in ("lambda_qlearner", "rho", "delta_sa"):
        if best.get(key) not in (None, "", "NA"):
            params[key] = float(best[key])
    return params


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


def run_job(instance, time_limit, selection, acceptance, params, rep, cores, folder,
            search_stats=False):
    """With search_stats, also saves iteration counts over time to
    stats_<instance>.json and adds their totals to the result file."""
    os.makedirs(folder, exist_ok=True)
    instance_path = os.path.join(INSTANCE_FOLDER, instance + ".json")
    solution_path = os.path.join(folder, "sol_{}.json".format(instance))
    result_path = os.path.join(folder, "result_{}.json".format(instance))
    stats_path = os.path.join(folder, "stats_{}.json".format(instance))
    seed = rep

    kwargs = dict(
        seed=seed,
        time_limit=time_limit,
        time_tolerance=TIME_TOLERANCE,
        verbose=False,
        heuristic_selection=selection,
        acceptance_selection=acceptance,
        sequence_length=params["sequence_length"],
        num_cores=cores,
        heuristic_set=HEURISTIC_SET,
        record_greedy_cycles=True,
        search_stats_file=stats_path if search_stats else None,
    )
    if "lambda_qlearner" in params:
        kwargs["lambda_q"] = params["lambda_qlearner"]
    if "rho" in params:
        kwargs["rho_r2r"] = params["rho"]
    if "delta_sa" in params:
        kwargs["delta_sa"] = params["delta_sa"]

    start = time.time()
    solution, _ = main(instance_path, **kwargs)
    elapsed = time.time() - start

    write_json(solution_path, solution)
    violations, cost = validate(instance_path, solution_path)

    greedy_file = os.path.join(GREEDY_FOLDER, "{}_seed{}.json".format(instance, seed))
    greedy = json.load(open(greedy_file)) if os.path.isfile(greedy_file) else {}

    search = {}
    if search_stats and os.path.isfile(stats_path):
        stats = json.load(open(stats_path))
        at_595 = next((s for s in stats["snapshots"] if s["event"] == "checkpoint_595s"), None)
        search = {
            "iterations": stats["iterations"],
            "candidates": stats["candidates"],
            "improving_candidates": stats["improving"],
            "new_best_solutions": stats["new_best"],
            "search_seconds": stats["seconds"],
            # State at IMADA's search time, for comparison with its runs
            "cost_at_595s": at_595["best_cost"] if at_595 else None,
            "candidates_at_595s": at_595["candidates"] if at_595 else None,
            "improving_at_595s": at_595["improving"] if at_595 else None,
        }

    # Written last: its presence marks the job as done
    write_json(result_path, {
        "instance": instance,
        "method": method_id(selection, acceptance),
        "selection": selection,
        "acceptance": acceptance,
        "replication": rep,
        "seed": seed,
        "cost": cost,
        "violations": violations,
        "feasible": violations == 0,
        # If the initial solution is infeasible, main() stops straight away and
        # the saved solution is the greedy one (no improvement phase).
        "initial_feasible": greedy.get("feasible"),
        "greedy_cycles": greedy.get("cycles"),
        "greedy_all_mandatory_admitted": greedy.get("all_mandatory_admitted"),
        "greedy_seconds": greedy.get("seconds"),
        **search,
        "time_limit": time_limit,
        "cores": cores,
        "params": params,
        "wall_seconds": elapsed,
        "host": os.uname().nodename,
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
    cores = int(os.environ.get("SLURM_CPUS_PER_TASK", 4))

    # Fail early on anything missing, before hours of runs
    missing = [
        i for instances, _ in INSTANCE_SETS.values() for i in instances
        if not os.path.isfile(os.path.join(INSTANCE_FOLDER, i + ".json"))
    ]
    if missing:
        sys.exit("Missing from {}: {}".format(INSTANCE_FOLDER, " ".join(missing)))
    if not os.path.isfile(VALIDATOR):
        sys.exit("Validator not found at {}. Compile it first.".format(VALIDATOR))
    params = {(s, a): tuned_params(s, a) for s in SELECTIONS for a in ACCEPTANCES}

    jobs = []
    for set_name, (instances, time_limit) in INSTANCE_SETS.items():
        for instance in instances:
            for selection in SELECTIONS:
                for acceptance in ACCEPTANCES:
                    folder = os.path.join(
                        SOLUTION_FOLDER, "{}core".format(cores),
                        method_id(selection, acceptance), "rep{:02d}".format(rep),
                    )
                    if os.path.isfile(os.path.join(folder, "result_{}.json".format(instance))):
                        continue
                    jobs.append((instance, time_limit, selection, acceptance, folder))

    hours = sum(j[1] for j in jobs) / 3600
    print("Replication {} (seed {}), {} cores: {} jobs to run, about {:.0f} h".format(
        rep, rep, cores, len(jobs), hours))

    for n, (instance, time_limit, selection, acceptance, folder) in enumerate(jobs, start=1):
        p = params[(selection, acceptance)]
        if args.dry_run:
            print("  {:10s} {:13s} {:5d} s  {}".format(
                instance, method_id(selection, acceptance), time_limit, p))
            continue
        print("[{}/{}] {} {}".format(n, len(jobs), instance, method_id(selection, acceptance)), flush=True)
        cost, violations = run_job(instance, time_limit, selection, acceptance, p, rep, cores, folder)
        print("  cost {} violations {}".format(cost, violations), flush=True)
