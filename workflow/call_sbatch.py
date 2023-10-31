""" 
Call all sbatch scripts within specified folder 
"""

import json
import os
import subprocess
import glob

# change permission of the script before running: chmod +x workflow.get_subreddit_data
ABS_PATH = "/N/u/baotruon/BigRed200/simsom"
SBATCH_FOLDERS = ["sbatch30", "sbatch33", "sbatch40", "sbatch41"]

for folder in SBATCH_FOLDERS:
    os.chdir(f"{ABS_PATH}/small_net_exps/{folder}")
    print(f"current dir: {os.getcwd()}")
    print(f"Add execution permission to all files")
    subprocess.run(["chmod", "-R", "+x", "."])

    fnames = glob.glob(f"/*.sh")
    output_dir = f"{ABS_PATH}/small_net_exps/output_{folder}"
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)
    print(f"current dir: {os.getcwd()}")
    for fname in fnames:
        print(f"Running ../{folder}/{fname}")
        # subprocess.run(
        #     [
        #         "sbatch",
        #         "../{folder}/{fname}",
        #     ]
        # )
