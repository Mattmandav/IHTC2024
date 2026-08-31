#!/bin/bash
#SBATCH -J STORMEDoff
#SBATCH -c 4
#SBATCH --array=1-30%25
#SBATCH --mail-user=m.davison2@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH -o ../output_ihtc_R2_save_over_time/%A_%a.out


DIRECTORY='./data/solutions/solutions_over_time'

srun uv run ~/IHTC2024_R2/run_save_over_time.py $DIRECTORY $SLURM_ARRAY_TASK_ID