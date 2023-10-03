#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=11
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=21
#SBATCH --time=1-23:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=phigamma_lessnodes

######  Module commands #####
source /N/u/baotruon/BigRed200/mambaforge/etc/profile.d/conda.sh
# conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running phigamma_lessnodes exps ######'
snakemake --nolock --snakefile workflow/more_rules/phigamma_multinodes.smk --cores 21