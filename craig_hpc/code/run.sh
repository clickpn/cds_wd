#!/bin/sh

#SBATCH --job-name=craig
#SBATCH --output=../slurm/slurm_%j.out
#SBATCH --error=../slurm/slurm_%j.err
#SBATCH --time=40:00:00
#SBATCH --nodes=2
#SBATCH --mem=40GB
#SBATCH --cpus-per-task=8
 
cd /scratch/sy1743/craig_hpc/code 
module load python/intel/2.7.12
pip install --user bs4

# you can replace path for keyword list
python craig.py --kws 'CA_kws.p'
