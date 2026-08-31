#!/bin/bash
#SBATCH -J IHTC_ENTRY_FINAL
#SBATCH -c 4
#SBATCH --array=1-20
#SBATCH -o ../output_ihtc/%A_%a.out
#SBATCH --mail-user=m.davison2@lancaster.ac.uk
#SBATCH --mail-type=end
#SBATCH --exclude=blackett

source ~/start-pyenv

DIRECTORY='./data/solutions/run'$SLURM_ARRAY_TASK_ID
if [ ! -d $DIRECTORY ]; then
  mkdir $DIRECTORY
fi

srun python ~/IHTC2024/run_storm.py $DIRECTORY