#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=24
#SBATCH --time=1-23:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=varymu

######  Module commands #####
source /N/u/baotruon/Carbonate/mambaforge/etc/profile.d/conda.sh
# conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/Carbonate/simsom
echo '###### running varymu exps ######'
snakemake --nolock --snakefile workflow/rules/vary_mu_multinodes.smk --cores 24