#!/bin/bash
#SBATCH --mem=100g
#SBATCH -p short,medium,backfill
#SBATCH -n 16
#SBATCH -N 1
#SBATCH --time=4:00:00
/home/bcov/sc/pipeline/protein_pipeline/worker.py $SLURM_JOB_ID 16 > $SLURM_JOB_ID.log 2>&1
