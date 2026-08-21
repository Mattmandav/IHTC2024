#!/bin/bash
#SBATCH -J STORMed_off
#SBATCH -c 4
#SBATCH --array=0-90%25
#SBATCH -o ../output_ihtc/%A_%a.out

DIRECTORY='./data/solutions_over_time'
if [ ! -d $DIRECTORY ]; then
  mkdir $DIRECTORY
fi

srun uv run ~/PATH_TO_STORM.py $DIRECTORY $SLURM_ARRAY_TASK_ID