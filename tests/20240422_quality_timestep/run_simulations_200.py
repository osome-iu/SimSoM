""" Script to run simulation(s)
    Parse command-line arguments specifying simulation parameters and output file paths 
    Run simulation(s)

    Reshare output file (.csv) and verbose tracking file (.json.gz) names are always suffixed by number of runs 
    e.g: if no_run=1, reshare_fpath="reshares_0.csv" and verboseout="verboseout_0.json.gz"
"""

try:
    from simsom import SimSom
    from simsom.graphutils import *
    import simsom.utils as utils
    from datetime import datetime
except ModuleNotFoundError:
    print(
        "Unable to import simsom package. \n"
        "Change to root directory of this project and run `pip install -e ./libs/`"
    )

import json
import numpy as np
import os
from copy import deepcopy


DATA_PATH = "/N/project/simsom/simsom_v3/10242023_v3.3/data"
network_fpath = os.path.join(DATA_PATH, "vary_network", "network_20.gml")

# G = init_net(**net_specs)
# G.write(network_fpath, format="gml")

RESULT_DIR = "/N/u/baotruon/BigRed200/simsom/tests/20240422_quality_timestep/results_maxsteps_200"
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

reshare_fpath = os.path.join(RESULT_DIR, "reshare.csv")
message_info_fpath = os.path.join(RESULT_DIR, "message_info.json.gz")

exp_config = "/N/project/simsom/simsom_v3/10242023_v3.3/config/vary_phigamma/02.json"

simulation_specs = json.load(open(exp_config, "r"))
simulation_specs["converge_by"] = "steps"
simulation_specs["max_steps"] = 200
simulation_specs["output_cascades"] = False
simulation_specs["save_message_info"] = False
# simulation_specs = {
#     "verbose": True,
#     "tracktimestep": True,
#     "save_message_info": True,
#     "output_cascades": True,
#     "epsilon": 0.0001,
#     "mu": 0.5,
#     "phi": 0,
# }
no_runs = 10

# Create a list to store results across runs
quality = []

print("*** Start simulation ***")
for run in range(no_runs):
    print(f"\n-- Run {run+1}/{no_runs}: \n\n Create SimSom instance..")
    now = datetime.now().strftime("%Y%m%d_%H%M")
    logger = utils.get_file_logger(
        log_dir="logs",
        full_log_path=os.path.join("logs", f"simulation_short_{run}__{now}.log"),
        also_print=True,
    )
    # Create a SimSom instance
    # avoid passing undefined keyword to InfoSys
    legal_specs = utils.remove_illegal_kwargs(simulation_specs, SimSom.__init__)
    legal_specs["logger"] = logger
    follower_sys = SimSom(network_fpath, **legal_specs)

    # Print parameters for sanity check
    if run == 0:
        print(follower_sys)

    # Run simulation
    if simulation_specs["output_cascades"] is False:
        results = follower_sys.simulation()
    else:
        results = follower_sys.simulation(
            reshare_fpath=reshare_fpath.replace(".csv", f"_{run}.csv")
        )
    print(f" - Simulation finished. Quality: {np.round(results['quality'],3)}")

    # Update the quality list
    quality += [results["quality"]]

    # Save verbose results (with simulation specs)
    if simulation_specs["save_message_info"] is True:
        specs = deepcopy(simulation_specs)
        specs.update(results)
        fpath = message_info_fpath.replace(".json.gz", f"_{run}.json.gz")
        utils.write_json_compressed(fpath, specs)

    # Save short results (with simulation specs)
    short_results = deepcopy(simulation_specs)
    short_results.update(results)
    json.dump(short_results, open(os.path.join(RESULT_DIR, f"results_{run}.json"), "w"))

print(f"*** Average quality across {no_runs} runs: {np.round(np.mean(quality),3)} ***")
