#!/bin/bash
#####  Constructed by HPC everywhere #####
#SBATCH -A r00382
#SBATCH --mail-user=baotruon@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=12
#SBATCH --time=2-23:59:00
#SBATCH --mem=16gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=v3

######  Module commands #####
source /N/u/baotruon/BigRed200/mambaforge/etc/profile.d/conda.sh
conda activate simsommodel


######  Job commands go below this line #####
cd /N/u/baotruon/BigRed200/simsom
echo '###### running v3 exps ######'
python3 experiments/10092023_comparev2/3.run_v3.py 100 1

echo '###### running v3 exps (alpha=15) ######'
python3 experiments/10092023_comparev2/3.run_v3.py 100 15