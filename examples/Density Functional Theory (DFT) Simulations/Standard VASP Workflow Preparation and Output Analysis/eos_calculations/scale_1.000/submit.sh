#!/bin/bash
#SBATCH -N 1
#SBATCH -n 48
#SBATCH -t 24:00:00
#SBATCH -p short
#SBATCH -C 6767P|6254|EPYC-9654|H100|H200|V100|L40S

srun --mpi=pmi2 vasp_std > vasp.out
