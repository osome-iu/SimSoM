#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=29
#SBATCH --time=3-23:59:00
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=thetagamma

######  Module commands #####
source /N/u/baotruon/Carbonate/miniconda3/etc/profile.d/conda.sh
conda activate simsom


######  Job commands go below this line #####
cd /N/slate/baotruon/simsom
echo '###### vary thetagamma ######'
snakemake --nolock --snakefile workflow/rules/thetagamma.smk --cores 29