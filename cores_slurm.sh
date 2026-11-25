#!/bin/bash
#SBATCH -J IHTC_CORES
#SBATCH -c 1
#SBATCH --array=1-10
#SBATCH -o ../output_ihtc_cores/%A_%a.out
#SBATCH --mail-user=a.d.page@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH --exclude=blackett

# r_sa_ours on all instances, 600 s per run, with the number of cores given
# by -c. Array task R runs replication R (seed R). Submit once per core count:
#   sbatch -c 1 cores_slurm.sh
#   sbatch -c 10 cores_slurm.sh
# Results go to data/solutions/<cores>core/r_sa_ours/, so the two runs (and
# the 4-core main results) never overwrite each other.
# Each task runs 93 instances of about 600 s, roughly 16 hours.
#
# Submit from the repo root, after: mkdir -p ../output_ihtc_cores
# Resubmitting skips instances that already have results.

cd "$SLURM_SUBMIT_DIR"

srun uv run run_cores.py
