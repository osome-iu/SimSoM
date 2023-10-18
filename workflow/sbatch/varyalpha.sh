#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=57
#SBATCH --time=3-23:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=alpha_full33

######  Module commands #####
source /N/u/baotruon/BigRed200/conda/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running alpha_full33 exps ######'
snakemake --rerun-incomplete --nolock --snakefile workflow/rules/varyalpha.smk --cores 57