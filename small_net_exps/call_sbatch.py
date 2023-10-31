""" 
Call all sbatch scripts within specified folder 
"""

import json
import os
import subprocess
import glob

# change permission of the script before running: chmod +x workflow.get_subreddit_data
ABS_PATH = "/N/u/baotruon/BigRed200/simsom"
SBATCH_FOLDERS = ["sbatch_30", "sbatch_33", "sbatch_40", "sbatch_41"]

for folder in SBATCH_FOLDERS:
    sbatch_dir = f"{ABS_PATH}/small_net_exps/{folder}"
    os.chdir(sbatch_dir)
    print(f"current dir: {os.getcwd()}")
    print(f"\t Add execution permission to all files")
    subprocess.run(["chmod", "-R", "+x", "."])

    fpaths = glob.glob(f"{sbatch_dir}/*.sh")
    output_dir = f"{ABS_PATH}/small_net_exps/output_{folder}"
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)
    print(f"Changed to output dir: {os.getcwd()}")
    for fpath in fpaths:
        print(f"\t Running {fpath}")
        subprocess.run(
            [
                "sbatch",
                f"{fpath}",
            ]
        )
