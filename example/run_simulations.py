try:
    from simsom import SimSom
    from simsom.graphutils import *
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

## Create network
# DATA_PATH = "experiments/08162023_delta/data"
# network_fpath = os.path.join(DATA_PATH, "infosys_network.gml")
network_fpath = "/Users/baott/SimSoM/example/data/infosys_network.gml"

RESULT_DIR = "/Users/baott/SimSoM/example/results_concurrent"
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
reshare_fpath = os.path.join(RESULT_DIR, "reshare.csv")
message_info_fpath = os.path.join(RESULT_DIR, "message_info.json.gz")

simulation_specs = {
    "verbose": True,
    "tracktimestep": True,
    "save_message_info": True,
    "output_cascades": True,
    "epsilon": 0.0001,
    "mu": 0.5,
    "phi": 1,
    "alpha": 15,
}

# Create a list to store results across runs
quality = []

print("*** Start simulation ***")
print(f"Create SimSom instance..")
# Create a SimSom instance
follower_sys = SimSom(network_fpath, **simulation_specs)
print(f"Parameters: {follower_sys.__repr__()}")
# Run simulation
if simulation_specs["output_cascades"] is False:
    results = follower_sys.simulation()
else:
    results = follower_sys.simulation(reshare_fpath=reshare_fpath)
print(f" - Simulation finished. Quality: {np.round(results['quality'],3)}")

# Update the quality list
quality += [results["quality"]]

# Save verbose results (with simulation specs)
if simulation_specs["save_message_info"] is True:
    specs = deepcopy(simulation_specs)
    specs.update(results)
    fpath = message_info_fpath
    fout = gzip.open(fpath, "w")
    write_json_compressed(fout, specs)

# Save short results (with simulation specs)
short_results = deepcopy(simulation_specs)
short_results.update({"quality": quality})
json.dump(short_results, open(os.path.join(RESULT_DIR, "results.json"), "w"))

print(
    f"*** Quality across: {np.round(np.mean(quality),3)} \pm {np.round(np.std(quality),3)} ***"
)
