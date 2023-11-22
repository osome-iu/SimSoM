#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=21
#SBATCH --time=3-23:59:00
#SBATCH --mem=58gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=phi_maxphi4_sm46zl5

######  Module commands #####
source /N/u/baotruon/BigRed200/conda/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running phi_maxphi4_sm46zl5 exps ######'
snakemake --nolock --rerun-triggers mtime --rerun-incomplete --snakefile sm_exps_nov21/rules_46zl5/phi_maxphi4.smk --cores 21