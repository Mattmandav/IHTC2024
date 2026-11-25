#!/bin/bash
#SBATCH -J IHTC_LONG
#SBATCH -c 4
#SBATCH --array=1-10
#SBATCH -o ../output_ihtc_long/%A_%a.out
#SBATCH --mail-user=a.d.page@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH --exclude=blackett
#SBATCH --time=8-00:00:00

# r_sa_ours on all instances for 2 hours per run on 4 cores, recording
# iterations, improving iterations and the best cost over time, to compare
# with the IMADA runs. Array task R runs replication R (seed R).
# Each task runs 93 instances of 2 hours, about 186 hours (7.75 days); the
# --time line above asks for 8 days. If the partition allows less, lower it:
# a task that is stopped keeps its finished instances, and resubmitting
# carries on from there.
#
# Submit from the repo root, after: mkdir -p ../output_ihtc_long
#   sbatch long_slurm.sh

cd "$SLURM_SUBMIT_DIR"

srun uv run run_long.py
