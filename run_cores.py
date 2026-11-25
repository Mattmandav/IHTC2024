"""
Core-count experiment: r_sa_ours (random selection, simulated annealing, our
heuristics, tuned parameters) on every instance, 600 s per run, with the
number of cores SLURM allocates. The candidate pool holds one solution per
core, so cores change how many candidates each iteration evaluates.

On STORM, cores_slurm.sh runs this as a job array: array task R runs
replication R with seed R. Submit it once per core count:
    sbatch -c 1 cores_slurm.sh
    sbatch -c 10 cores_slurm.sh
The 4-core results already exist from instances_slurm.sh.

By hand, from the repo root:
    uv run run_cores.py 3 --cores 10           run replication 3 on 10 cores
    uv run run_cores.py 3 --cores 10 --dry-run list its jobs

Output, next to the main results:
    data/solutions/<cores>core/r_sa_ours/rep<RR>/sol_<instance>.json
    data/solutions/<cores>core/r_sa_ours/rep<RR>/result_<instance>.json
A job whose result file exists is skipped, so a resubmitted task resumes.
"""

import argparse
import os
import sys

from run_instances import (
    INSTANCE_FOLDER, INSTANCE_SETS, SOLUTION_FOLDER, VALIDATOR,
    method_id, run_job, tuned_params,
)

SELECTION, ACCEPTANCE = "random", "sa"
TIME_LIMIT = 600

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("replication", nargs="?", type=int,
                        help="replication number (default: the SLURM array task ID)")
    parser.add_argument("--cores", type=int,
                        help="cores to use (default: what SLURM allocated)")
    parser.add_argument("--dry-run", action="store_true", help="list the jobs and stop")
    args = parser.parse_args()

    rep = args.replication
    if rep is None:
        if "SLURM_ARRAY_TASK_ID" not in os.environ:
            parser.error("give a replication number, or run inside a SLURM array")
        rep = int(os.environ["SLURM_ARRAY_TASK_ID"])
    if rep < 1:
        parser.error("replications are numbered from 1")
    cores = args.cores or int(os.environ.get("SLURM_CPUS_PER_TASK", 0))
    if cores < 1:
        parser.error("give --cores, or run inside SLURM")

    instances = [i for names, _ in INSTANCE_SETS.values() for i in names]
    missing = [i for i in instances if not os.path.isfile(os.path.join(INSTANCE_FOLDER, i + ".json"))]
    if missing:
        sys.exit("Missing from {}: {}".format(INSTANCE_FOLDER, " ".join(missing)))
    if not os.path.isfile(VALIDATOR):
        sys.exit("Validator not found at {}. Compile it first.".format(VALIDATOR))
    params = tuned_params(SELECTION, ACCEPTANCE)

    method = method_id(SELECTION, ACCEPTANCE)
    folder = os.path.join(SOLUTION_FOLDER, "{}core".format(cores), method, "rep{:02d}".format(rep))
    jobs = [i for i in instances
            if not os.path.isfile(os.path.join(folder, "result_{}.json".format(i)))]
    print("{} on {} cores, replication {} (seed {}): {} jobs to run, about {:.1f} h".format(
        method, cores, rep, rep, len(jobs), len(jobs) * TIME_LIMIT / 3600))

    for n, instance in enumerate(jobs, start=1):
        if args.dry_run:
            print("  " + instance)
            continue
        print("[{}/{}] {}".format(n, len(jobs), instance), flush=True)
        cost, violations = run_job(instance, TIME_LIMIT, SELECTION, ACCEPTANCE,
                                   params, rep, cores, folder)
        print("  cost {} violations {}".format(cost, violations), flush=True)
