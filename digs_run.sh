#!/bin/bash
#SBATCH --mem=100g
#SBATCH -p short,medium,backfill
#SBATCH -n 16
#SBATCH -N 1
#SBATCH --time=8:00:00
stdbuf -oL -eL /home/bcov/sc/pipeline/protein_pipeline/worker.py $SLURM_JOB_ID 16 > $SLURM_JOB_ID.log 2>&1
