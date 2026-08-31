#!/bin/bash
#SBATCH -J STORMed_off
#SBATCH -c 4
#SBATCH --array=0-32%25
#SBATCH --mail-user=m.davison2@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH -o ../output_ihtc_R2_supplementary/%A_%a.out


DIRECTORY='./data/solutions/supplementary'
if [ ! -d $DIRECTORY ]; then
  mkdir $DIRECTORY
fi

srun uv run ~/IHTC2024_R2/run_supplementary.py $DIRECTORY $SLURM_ARRAY_TASK_ID