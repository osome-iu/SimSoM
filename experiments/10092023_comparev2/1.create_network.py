try:
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

ABS_PATH = "/N/project/simsom/simsom_v3/10092023_compare_v2"
DATA_PATH = os.path.join(ABS_PATH, "data")
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# humannet_fpath = os.path.join(DATA_PATH, "follower_network.gml")
network_fpath = os.path.join(DATA_PATH, "infosys_network_10k.gml")

net_specs = {
    "targeting_criterion": None,
    "human_network": None,
    "n_humans": 10000,
    "beta": 0.05,  # 50 bot
    "gamma": 0.01,  # each has 10 followers
    "verbose": True,
}

G = init_net(**net_specs)
G.write(network_fpath, format="gml")
