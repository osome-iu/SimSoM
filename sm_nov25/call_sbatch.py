""" 
Call all sbatch scripts within specified folder 
"""

import json
import os
import subprocess
import glob

# change permission of the script before running: chmod +x workflow.get_subreddit_data
ABS_PATH = "/N/u/baotruon/BigRed200/simsom"
SBATCH_FOLDERS = ["sbatch_46zl", "sbatch_46zl5"]

for folder in SBATCH_FOLDERS:
    sbatch_dir = f"{ABS_PATH}/sm_nov25/{folder}"
    os.chdir(sbatch_dir)
    print(f"current dir: {os.getcwd()}")
    print(f"\t Add execution permission to all files")
    subprocess.run(["chmod", "-R", "+x", "."])

    fpaths = glob.glob(f"{sbatch_dir}/*.sh")
    output_dir = f"{ABS_PATH}/sm_new_exps/output_{folder}"
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)
    print(f"Changed to output dir: {os.getcwd()}")
    for fpath in fpaths:
        if "cascade_scaling" in fpath:
            continue
        print(f"\t Running {fpath}")
        subprocess.run(
            [
                "sbatch",
                f"{fpath}",
            ]
        )
