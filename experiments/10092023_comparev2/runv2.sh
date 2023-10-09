#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=5
#SBATCH --time=2-23:59:00
#SBATCH --mem=16gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=v2

######  Module commands #####
source /N/u/baotruon/BigRed200/mambaforge/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running v2 exps (alpha=1) ######'
python3 experiments/10092023_comparev2/2.run_v2.py 1 100