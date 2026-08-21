#!/bin/bash
#SBATCH -J STORMed_off
#SBATCH -c 4
#SBATCH --array=1-20
#SBATCH -o ./hidden_%A_%a.out


DIRECTORY='./data/solutions/run'$SLURM_ARRAY_TASK_ID
if [ ! -d $DIRECTORY ]; then
  mkdir $DIRECTORY
fi

srun uv run ~/run_hidden.py $DIRECTORY