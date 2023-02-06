"""
    Minimal example for running simulation
"""
from simsom.InfoSys import InfoSystem
import simsom.graphutils as graphutils
import json
import numpy as np
from collections import defaultdict
import os

DATA_PATH = "example/data"


def run_simulation(
    net_specs,
    infosys_specs,
    runs=10,
    reshare_fpath=os.path.join("example", "reshares.csv"),
):
    G = graphutils.init_net(**net_specs)

    network_fpath = os.path.join(DATA_PATH, "infosys_network.gml")
    G.write(network_fpath, format="gml")

    n_measures = defaultdict(lambda: [])

    quality = []
    print("Start simulation ..")
    for run in range(runs):
        print("Create InfoSystem instance..")
        follower_sys = InfoSystem(network_fpath, **infosys_specs)
        if (
            "output_cascades" in infosys_specs.keys()
            and infosys_specs["output_cascades"] is True
        ):
            verbose_results = follower_sys.simulation(
                reshare_fpath=reshare_fpath.replace(".csv", f"_{run}.csv"),
                exposure_fpath=os.path.join(
                    os.path.dirname(reshare_fpath), f"exposure_{run}.csv"
                ),
            )
        else:
            verbose_results = follower_sys.simulation()
        quality += [verbose_results["quality"]]

        # Update results over multiple simulations
        for k, val in verbose_results.items():
            n_measures[k] += [val]

    print(f"*** Average quality: {np.round(np.mean(quality),3)} ***")
    print(len(quality))
    return n_measures


BETA = 0.1
GAMMA = 0.05
EPSILON = 0.0001

none_specs = {
    "targeting_criterion": None,
    "human_network": os.path.join(DATA_PATH, "follower_network.gml"),
    "n_humans": 50,
    # "beta": 0.02,
    # "gamma": 0.04,
    "beta": BETA,  # 2 bot
    "gamma": GAMMA,  # each has 5 followers
    "verbose": True,
}

infosys_specs = {
    "tracktimestep": True,
    "verbose": False,
    "epsilon": EPSILON,
    "mu": 0.5,
    "phi": 1,
    "alpha": 15,
}
print(os.path.dirname("example/data"))
results = run_simulation(none_specs, infosys_specs, runs=2)
json.dump(results, open(os.path.join("example", "results.json"), "w"))

print("Finish saving results!")

