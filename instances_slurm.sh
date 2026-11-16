#!/bin/bash
#SBATCH -J IHTC_INSTANCES
#SBATCH -c 4
#SBATCH --array=1-20
#SBATCH -o ../output_ihtc_instances/%A_%a.out
#SBATCH --mail-user=a.d.page@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH --exclude=blackett

# Results for all instances and all selection/acceptance configurations, our
# heuristics, tuned parameters from irace_results/.
# Array task R runs replication R (seed R), so --array=1-20 gives 20
# replications. Cores come from -c and are part of the output folder name
# (data/solutions/4core/...), so a run with -c 1 or -c 10 doesn't overwrite it.
#
# Submit from the repo root:
#   mkdir -p ../output_ihtc_instances      (SLURM won't create it)
#   sbatch instances_slurm.sh
# Resubmitting skips jobs that already have results.

cd "$SLURM_SUBMIT_DIR"

srun uv run run_instances.py
