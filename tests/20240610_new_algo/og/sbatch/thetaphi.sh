#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=35
#SBATCH --time=3:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=og_algo_phi

######  Module commands #####
source /N/u/baotruon/BigRed200/conda/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running og_algo_phi exps ######'
snakemake --nolock --rerun-triggers mtime --rerun-incomplete --snakefile /N/u/baotruon/BigRed200/simsom/tests/20240610_new_algo/og/rules/thetaphi.smk --cores 35