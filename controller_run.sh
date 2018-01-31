#!/bin/bash
#SBATCH --mem=12g
#SBATCH -p long
#SBATCH -n 1
#SBATCH -N 1
stdbuf -oL -eL /home/bcov/sc/pipeline/protein_pipeline/controller.py $SLURM_JOB_ID 1 > controller_$SLURM_JOB_ID.log 2>&1
