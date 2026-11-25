"""
Long-run experiment: r_sa_ours (random selection, simulated annealing, our
heuristics, tuned parameters) on every instance for 2 hours per run on 4
cores, recording how the search progresses so it can be compared with the
IMADA solver's runs (run_imada.py).

On STORM, long_slurm.sh runs this as a job array: array task R runs
replication R with seed R. Each task runs 93 instances of 2 hours, about
186 hours (7.75 days).

By hand, from the repo root:
    uv run run_long.py 3              run replication 3
    uv run run_long.py 3 --dry-run    list its jobs

Output (a separate folder, so it never mixes with the 600 s results):
    data/solutions/4core_7200s/r_sa_ours/rep<RR>/sol_<instance>.json
    data/solutions/4core_7200s/r_sa_ours/rep<RR>/stats_<instance>.json
    data/solutions/4core_7200s/r_sa_ours/rep<RR>/result_<instance>.json

stats_<instance>.json holds the totals (iterations, candidates evaluated,
improving candidates, new best solutions, best cost) and snapshots of them
at every new best and at 60, 300, 595, 600, 1200, 1800, 3600 and 5400 s of
search, plus the end. The result file repeats the totals and the state at
595 s, IMADA's search time. A job whose result file exists is skipped, so a
resubmitted task resumes.
"""

import argparse
import os
import sys

from run_instances import (
    INSTANCE_FOLDER, INSTANCE_SETS, SOLUTION_FOLDER, VALIDATOR,
    method_id, run_job, tuned_params,
)

SELECTION, ACCEPTANCE = "random", "sa"
TIME_LIMIT = 7200
CORES = 4

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("replication", nargs="?", type=int,
                        help="replication number (default: the SLURM array task ID)")
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
        sys.exit("This experiment uses {} cores; submit with -c {} (got {}).".format(
            CORES, CORES, allocated))

    instances = [i for names, _ in INSTANCE_SETS.values() for i in names]
    missing = [i for i in instances if not os.path.isfile(os.path.join(INSTANCE_FOLDER, i + ".json"))]
    if missing:
        sys.exit("Missing from {}: {}".format(INSTANCE_FOLDER, " ".join(missing)))
    if not os.path.isfile(VALIDATOR):
        sys.exit("Validator not found at {}. Compile it first.".format(VALIDATOR))
    params = tuned_params(SELECTION, ACCEPTANCE)

    method = method_id(SELECTION, ACCEPTANCE)
    folder = os.path.join(SOLUTION_FOLDER, "{}core_{}s".format(CORES, TIME_LIMIT),
                          method, "rep{:02d}".format(rep))
    jobs = [i for i in instances
            if not os.path.isfile(os.path.join(folder, "result_{}.json".format(i)))]
    print("{} for {} s on {} cores, replication {} (seed {}): {} jobs to run, about {:.0f} h".format(
        method, TIME_LIMIT, CORES, rep, rep, len(jobs), len(jobs) * TIME_LIMIT / 3600))

    for n, instance in enumerate(jobs, start=1):
        if args.dry_run:
            print("  " + instance)
            continue
        print("[{}/{}] {}".format(n, len(jobs), instance), flush=True)
        cost, violations = run_job(instance, TIME_LIMIT, SELECTION, ACCEPTANCE,
                                   params, rep, CORES, folder, search_stats=True)
        print("  cost {} violations {}".format(cost, violations), flush=True)
