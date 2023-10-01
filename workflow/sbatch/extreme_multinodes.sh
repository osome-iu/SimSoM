#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=21
#SBATCH --time=3-23:59:00
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=extreme_multinodes

######  Module commands #####
source /N/u/baotruon/Carbonate/mambaforge/etc/profile.d/conda.sh
# conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/Carbonate/simsom
echo '###### running extreme_multinodes exps ######'
snakemake --nolock --snakefile workflow/rules/extreme_multinodes.smk --cores 21