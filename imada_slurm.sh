#!/bin/bash
#SBATCH -J IHTC_IMADA
#SBATCH -c 4
#SBATCH --array=1-10
#SBATCH -o ../output_ihtc_imada/%A_%a.out
#SBATCH --mail-user=a.d.page@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH --exclude=blackett

# The SDU-IMADA solver on all instances used by instances_slurm.sh, on the
# same hardware settings. Array task R runs replication R (seed R): keep
# --array the same as in instances_slurm.sh so both get the same replications.
# Each task runs 93 instances of about 600 s, roughly 16 hours.
#
# Submit from the repo root:
#   bash imada_solver/build.sh             (once, on the login node)
#   mkdir -p ../output_ihtc_imada          (SLURM won't create it)
#   sbatch imada_slurm.sh
# Resubmitting skips instances that already have results.

cd "$SLURM_SUBMIT_DIR"

srun uv run run_imada.py
