#!/bin/bash
#SBATCH -J STORMed_off
#SBATCH -c 10
#SBATCH --array=1-20%10
#SBATCH --mail-user=m.davison2@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH -o ../output_ihtc_R2_sa/%A_%a.out


DIRECTORY='./data/solutions/run'$SLURM_ARRAY_TASK_ID
if [ ! -d $DIRECTORY ]; then
  mkdir $DIRECTORY
fi

srun uv run ~/IHTC2024_R2/run_public_10_core.py $DIRECTORY