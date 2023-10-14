try:
    from simsom.graphutils import *
    from simsom.modelv2_debug import SimSomV2
    from simsom.utils import *
except ModuleNotFoundError:
    print(
        "Unable to import simsom package. \n"
        "Change to root directory of this project and run `pip install -e ./libs/`"
    )

import json
import numpy as np
import os
from copy import deepcopy
from collections import defaultdict

# Suppress warnings
import warnings

warnings.filterwarnings("ignore")

ABS_PATH = "experiments/10132023_compare_message_age"
DATA_PATH = os.path.join(ABS_PATH, "data")
log_dir = os.path.join(ABS_PATH, "logs")

net_specs = {
    "targeting_criterion": None,
    "human_network": None,
    "n_humans": 1000,
    "beta": 0,  # 50 bot
    "gamma": 0,  # each has 10 followers
    "verbose": True,
}

network_fpath = os.path.join(DATA_PATH, "nobot_network.gml")
G = init_net(**net_specs)
G.write(network_fpath, format="gml")

## SPECS
alpha = 15
verbose = True
simulation_specs = {
    "verbose": verbose,
    "tracktimestep": True,
    "save_memeinfo": False,
    "output_cascades": False,
    "epsilon": 0.0001,
    "mu": 0.5,
    "alpha": alpha,
}
no_runs = 1

## ADD LOGGING
logger = get_file_logger(
    log_dir=log_dir,
    log_fpath=os.path.join(log_dir, f"run_v2__alpha{alpha}__verbose{verbose}.log"),
    also_print=True,
)
simulation_specs["logger"] = logger

## OLD MODEL

RESULT_V2 = os.path.join(ABS_PATH, "results_baseline/v2")
reshare_fpath = os.path.join(RESULT_V2, f"reshare_alpha{alpha}.csv")
exposure_fpath = os.path.join(RESULT_V2, f"exposure_alpha{alpha}.csv")
message_info_fpath = os.path.join(RESULT_V2, f"message_info_alpha{alpha}.json.gz")

if not os.path.exists(RESULT_V2):
    os.makedirs(RESULT_V2)

# RUN SIMS

# Create a list to store results across runs
# quality = []

metrics = ["quality", "diversity", "discriminative_pow"]
res_list = defaultdict(list)

print("*** Start simulation ***")
for run in range(no_runs):
    print(f"-- Run {run+1}/{no_runs}: \n Create SimSom instance..")
    if run == 0:
        simulation_specs_ = deepcopy(simulation_specs)
        simulation_specs_["save_memeinfo"] = True
        follower_sys = SimSomV2(network_fpath, **simulation_specs_)
        print(follower_sys)

    else:
        # Create a SimSom instance
        follower_sys = SimSomV2(network_fpath, **simulation_specs)

    # Run simulation
    if simulation_specs["output_cascades"] is False:
        results = follower_sys.simulation()
    else:
        results = follower_sys.simulation(
            reshare_fpath=reshare_fpath.replace(".csv", f"_{run}.csv"),
            exposure_fpath=exposure_fpath.replace(".csv", f"_{run}.csv"),
        )
    print(f" - Simulation finished. Quality: {np.round(results['quality'],3)}")

    # Update the metric list
    # quality += [results["quality"]]
    for metric in metrics:
        res_list[metric] += [results[metric]]

    # Save verbose results (with simulation specs)
    if run == 0:
        # if simulation_specs["save_memeinfo"] is True:
        specs = deepcopy(simulation_specs)
        specs.update(results)
        fpath = message_info_fpath.replace(".json.gz", f"_{run}.json.gz")
        fout = gzip.open(fpath, "w")
        write_json_compressed(fout, specs)

# Save short results (with simulation specs)
simulation_specs.pop("logger")
short_results = deepcopy(simulation_specs)
short_results.update(res_list)
json.dump(
    short_results, open(os.path.join(RESULT_V2, f"results_alpha{alpha}.json"), "w")
)

print(
    f"*** V2 Average quality across {no_runs} runs: {np.round(np.mean(res_list['quality']),3)} ***"
)
