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

# Suppress warnings
import warnings

warnings.filterwarnings("ignore")

DATA_PATH = "experiments/10092023_compare_alpha1/data"
net_specs = {
    "targeting_criterion": None,
    "human_network": None,
    "n_humans": 3,
    "beta": 0.4,  # 1 bot
    "gamma": 0.7,  # each has 2 followers
    "verbose": True,
}

## SPECS
alpha = 1
verbose = True
simulation_specs = {
    "verbose": verbose,
    "tracktimestep": True,
    "save_memeinfo": False,
    "output_cascades": False,
    "epsilon": 0.0001,
    "mu": 0.5,
    "phi": 1,
    "alpha": alpha,
}
log_dir = "experiments/10092023_compare_alpha1/results_debug/logs"
logger = get_file_logger(
    log_dir=log_dir,
    log_fpath=os.path.join(log_dir, f"run_v2__alpha{alpha}__verbose{verbose}.log"),
    also_print=True,
)
simulation_specs["logger"] = logger

## CREATE NETWORK
network_fpath = os.path.join(DATA_PATH, "4nodes_network.gml")
# G = init_net(**net_specs)

# df = G.get_edge_dataframe()
# df_vert = G.get_vertex_dataframe()
# df["source"].replace(df_vert["uid"], inplace=True)
# df["target"].replace(df_vert["uid"], inplace=True)
# df_vert.set_index("uid", inplace=True)  # Optional
# logger.info(df)
# G.write(network_fpath, format="gml")

## OLD MODEL

RESULT_V2 = "experiments/10092023_compare_alpha1/results_debug/v2"
reshare_fpath = os.path.join(RESULT_V2, f"reshare_alpha{alpha}.csv")
exposure_fpath = os.path.join(RESULT_V2, f"exposure_alpha{alpha}.csv")
message_info_fpath = os.path.join(RESULT_V2, f"message_info_alpha{alpha}.json.gz")

if not os.path.exists(RESULT_V2):
    os.makedirs(RESULT_V2)

# RUN SIMS


# Create a list to store results across runs
quality = []

print("*** Start simulation ***")

# Create a SimSom instance
follower_sys = SimSomV2(network_fpath, **simulation_specs)
# Run simulation
if simulation_specs["output_cascades"] is False:
    results = follower_sys.simulation()
else:
    results = follower_sys.simulation(
        reshare_fpath=reshare_fpath,
        exposure_fpath=exposure_fpath,
    )
print(f" - Simulation finished. Quality: {np.round(results['quality'],3)}")

# Update the quality list
quality += [results["quality"]]

# Save verbose results (with simulation specs)
if simulation_specs["save_memeinfo"] is True:
    specs = deepcopy(simulation_specs)
    specs.update(results)
    fpath = message_info_fpath
    fout = gzip.open(fpath, "w")
    write_json_compressed(fout, specs)

# Save short results (with simulation specs)
short_results = deepcopy(simulation_specs)
short_results.update({"quality": quality})
short_results.pop("logger", "")
json.dump(
    short_results,
    open(os.path.join(RESULT_V2, f"results_alpha{alpha}.json"), "w"),
)
