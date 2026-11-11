#!/bin/bash
#SBATCH -J IHTC_IRACE
#SBATCH -c 4
#SBATCH --array=1-27
#SBATCH -o ../output_ihtc_irace/%A_%a.out
#SBATCH --mail-user=m.davison2@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH --exclude=blackett

# One irace configuration per array task (uv run run_irace.py --list shows them):
#   1-9   our heuristics, 10-18 IMADA heuristics, 19-27 both
# Each task runs 300 experiments of 600 s, about 50 hours. irace only writes
# its CSV at the end, so make sure the partition's time limit allows that.
#
# Before submitting (once):
#   mkdir -p ../output_ihtc_irace                      # SLURM will not create it
#   uv sync                                            # avoid 27 tasks syncing at once
#   uv run python imada_bridge/setup.py build_ext --inplace   # needs GCC 11+

source ~/start-pyenv

# run_irace.py uses paths relative to the repo root (main.py, data/instances, CSVs)
REPO=~/IHTC2024
cd $REPO

srun uv run run_irace.py $SLURM_ARRAY_TASK_ID
