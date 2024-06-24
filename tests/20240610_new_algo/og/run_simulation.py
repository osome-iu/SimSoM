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
import simsom.utils as utils

# Suppress warnings
import warnings

warnings.filterwarnings("ignore")

## Create network


RESULT_DIR = "/N/u/baotruon/BigRed200/simsom/tests/20240610_new_algo/v1/results"
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
# Use formatted current date and time as logging file name
current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d.%H%M%S")

outfile = os.path.join(RESULT_DIR, f"results__{formatted_datetime}.json")
reshare_fpath = os.path.join(RESULT_DIR, f"reshare__{formatted_datetime}.csv")
exposure_fpath = os.path.join(RESULT_DIR, f"exposure__{formatted_datetime}.csv")
message_info_fpath = os.path.join(
    RESULT_DIR, f"message_info__{formatted_datetime}.json.gz"
)


DATA_PATH = "/N/project/simsom/simsom_v3/10242023_v3.3/"
network_fpath = os.path.join(DATA_PATH, "data", "vary_network", "network_33.gml")

simulation_specs = json.load(
    open(
        os.path.join(DATA_PATH, "config", "vary_gamma", "None0.json"),
        "r",
    )
)
simulation_specs["epsilon"] = 0.01
simulation_specs["n_threads"] = 1


## LOGGING
log_dir = f"{os.path.dirname(outfile)}/logs"

logger = utils.get_file_logger(
    log_dir=log_dir,
    full_log_path=os.path.join(
        log_dir,
        f"{os.path.basename(outfile).replace('.json',f'__{formatted_datetime}.log')}",
    ),
    also_print=True,
)

# Create a list to store results across runs
quality = []

logger.info("*** Start simulation ***")
logger.info(f"Create SimSom instance..")
# Create a SimSom instance
# avoid passing undefined keyword to InfoSys
legal_specs = utils.remove_illegal_kwargs(simulation_specs, SimSom.__init__)
follower_sys = SimSom(network_fpath, **legal_specs)
logger.info(f"Parameters: {follower_sys.__repr__()}")
# Run simulation
if simulation_specs["output_cascades"] is False:
    results = follower_sys.simulation()
else:
    results = follower_sys.simulation(reshare_fpath=reshare_fpath)
logger.info(f" - Simulation finished. Quality: {np.round(results['quality'],3)}")

# Update the quality list
quality += [results["quality"]]

# Save verbose results (with simulation specs)
# if simulation_specs["save_message_info"] is True:
specs = deepcopy(simulation_specs)
specs.update(results)
fpath = message_info_fpath
# fout = gzip.open(fpath, "w")
utils.write_json_compressed(fpath, specs)

# Save short results (with simulation specs)
short_results = deepcopy(simulation_specs)
short_results.update({"quality": quality})
json.dump(short_results, open(outfile, "w"))

logger.info(f"*** Quality across: {np.round(np.mean(quality),3)} ***")
