try:
    from simsom.graphutils import *
    from simsom.model import SimSom
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

DATA_PATH = "experiments/10172023_v3.0_exps/data_10212023"
net_specs = {
    "targeting_criterion": None,
    "human_network": None,
    "n_humans": 1000,
    "beta": 0.05,  # 50 bot
    "gamma": 0.01,  # each has 10 followers
    "verbose": True,
}

network_fpath = os.path.join(DATA_PATH, "infosys_network.gml")
# G = init_net(**net_specs)
# G.write(network_fpath, format="gml")

# network_fpath = os.path.join(DATA_PATH, "network_baseline.gml")
## SPECS
alpha = 15
simulation_specs = {
    "verbose": False,
    "tracktimestep": True,
    "save_message_info": False,
    "output_cascades": False,
    "epsilon": 0.001,
    "mu": 0.5,
    "alpha": alpha,
    "n_threads": 12,
}
no_runs = 1

## OLD MODEL

RESULT_DIR = "experiments/10142023_v3.3_exps/results_local"
reshare_fpath = os.path.join(RESULT_DIR, f"reshare_alpha{alpha}.csv")
exposure_fpath = os.path.join(RESULT_DIR, f"exposure_alpha{alpha}.csv")
message_info_fpath = os.path.join(RESULT_DIR, f"message_info_alpha{alpha}.json.gz")

if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

# RUN SIMS

# Create a list to store results across runs
# quality = []

metrics = ["quality", "diversity", "discriminative_pow", "age_timestep"]
res_list = defaultdict(list)

print("*** Start simulation ***")
for run in range(no_runs):
    print(f"-- Run {run+1}/{no_runs}: \n Create SimSom instance..")
    if run == 0:
        simulation_specs_ = deepcopy(simulation_specs)
        simulation_specs_["save_message_info"] = True
        follower_sys = SimSom(network_fpath, **simulation_specs_)
        print(follower_sys)

    else:
        # Create a SimSom instance
        follower_sys = SimSom(network_fpath, **simulation_specs)

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
        # if simulation_specs["save_message_info"] is True:
        specs = deepcopy(simulation_specs)
        specs.update(results)
        fpath = message_info_fpath.replace(".json.gz", f"_{run}.json.gz")
        write_json_compressed(fpath, specs)

# Save short results (with simulation specs)
short_results = deepcopy(simulation_specs)
short_results.update(res_list)
json.dump(
    short_results, open(os.path.join(RESULT_DIR, f"results_alpha{alpha}.json"), "w")
)

print(
    f"*** Average quality across {no_runs} runs: {np.round(np.mean(res_list['quality']),3)} ***"
)
