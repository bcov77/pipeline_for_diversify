#!/bin/bash
#SBATCH --mem=100g
#SBATCH -p short,medium,backfill
#SBATCH -n 16
#SBATCH -N 1
#SBATCH --time=8:00:0
id=$SLURM_JOB_ID$(date +%Y%m%d%H%M%S)
stdbuf -oL -eL /home/bcov/sc/pipeline/protein_pipeline/worker.py $id 16 > $id.log 2>&10
