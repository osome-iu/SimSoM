#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=43
#SBATCH --time=3-23:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=mu_sm33

######  Module commands #####
source /N/u/baotruon/BigRed200/conda/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running mu_sm33 exps ######'
snakemake --rerun-incomplete --nolock --snakefile experiments/10242023_v3.3_exps/rules/varymu.smk --cores 43