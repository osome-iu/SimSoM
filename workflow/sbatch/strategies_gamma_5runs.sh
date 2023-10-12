#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=43
#SBATCH --time=3-23:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=strategie_5runs

######  Module commands #####
source /N/u/baotruon/BigRed200/conda/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running strategie_5runs exps ######'
snakemake --rerun-incomplete --nolock --snakefile workflow/rules/strategies_gamma_5runs.smk --cores 43