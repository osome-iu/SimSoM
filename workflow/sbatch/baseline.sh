#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=21
#SBATCH --time=1-23:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=baseline

######  Module commands #####
source /N/u/baotruon/BigRed200/mambaforge/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running baseline exps ######'
snakemake --nolock --snakefile workflow/rules/baseline.smk --cores 21