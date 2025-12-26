#!/bin/bash
#SBATCH -N 1
#SBATCH -n 40
#SBATCH -t 24:00:00
#SBATCH -p short
#SBATCH --job-name=masgent_job
#SBATCH --output=masgent_job.out
#SBATCH --error=masgent_job.err

srun --mpi=pmi2 vasp_std > vasp.out
