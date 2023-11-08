""" Script to run simulations """

from simsom.model_46z import SimSom
import simsom.utils as utils

import gzip
import sys
import argparse
import json
import numpy as np
import copy
from collections import defaultdict
import os


def multiple_simulations(
    infosys_specs, times=1, reshare_fpath="reshares.csv", verboseout=None
):
    # baseline:  mu=0.5, alpha=15, beta=0.01, gamma=0.001, phi=1, theta=1
    # cascade data file name has format: f"{basedir}{exp_name}__{cascade_type}_{run_no}.csv"
    metrics = ["quality", "diversity", "discriminative_pow", "model"]
    n_measures = defaultdict(lambda: [])

    print(f"Run simulation {times} times..")
    for time in range(times):
        print(f"**{time+1}/{times}**")
        try:
            print("Create SimSom instance..")
            follower_sys = SimSom(**infosys_specs)
            print("Start simulation ..")
            # Tracking cascade info
            if infosys_specs["output_cascades"] is True:
                #  make a reshare.csv file no matter what. Save to other files according to number of (multiple) runs.
                if time > 0:
                    prefix = f"_{time}.csv"
                else:
                    prefix = f".csv"
                measurements = follower_sys.simulation(
                    reshare_fpath=reshare_fpath.replace(".csv", prefix)
                )
            else:
                measurements = follower_sys.simulation()

        except Exception as e:
            raise Exception("Failed to run simulations.", e)

        try:
            # Update results over multiple simulations
            for metric in metrics:
                n_measures[metric] += [measurements[metric]]

            # Save verbose results
            if verboseout is not None:
                if time > 0:
                    prefix = f"_{time}.json.gz"
                else:
                    prefix = f".json.gz"

                verboseout_path = verboseout.replace(".json.gz", prefix)
                specs = copy.deepcopy(infosys_specs)
                specs.update(measurements)
                utils.write_json_compressed(verboseout_path, specs)

        except Exception as e:
            raise ("Error saving verbose results", e)

    print(
        f"average quality for follower network: {np.mean(np.array(n_measures['quality']))} pm {np.std(np.array(n_measures['quality']))}"
    )

    # return a short version of measurements
    return dict(n_measures)


def run_simulation(infosys_specs, reshare_fpath="reshares.csv"):
    # baseline:  mu=0.5, alpha=15, beta=0.01, gamma=0.001, phi=1, theta=1
    print("Create SimSom instance..")
    follower_sys = SimSom(**infosys_specs)
    print(f"Start simulation..")
    dir = os.path.dirname(reshare_fpath)
    exp_name = os.path.basename(reshare_fpath).split("__")[0]
    measurements = follower_sys.simulation(reshare_fpath=reshare_fpath)
    print("average quality for follower network:", measurements["quality"])
    return measurements


def main(args):
    # TODO: remove mode
    parser = argparse.ArgumentParser(
        description="run simulation on an igraph instance of SimSom",
    )

    parser.add_argument(
        "-i",
        "--infile",
        action="store",
        dest="infile",
        type=str,
        required=True,
        help="path to input gml file of network",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        action="store",
        dest="outfile",
        type=str,
        required=True,
        help="path to .json file containing infosys measurements",
    )
    parser.add_argument(
        "-r",
        "--resharefpath",
        action="store",
        dest="resharefpath",
        type=str,
        required=False,
        help="path to .csv file containing reshare cascade info",
    )
    parser.add_argument(
        "-v",
        "--verboseoutfile",
        action="store",
        dest="verboseoutfile",
        type=str,
        required=False,
        help="path to .json.gz file containing verbose infosys measurements (track all messages & feeds)",
    )
    parser.add_argument(
        "--config",
        action="store",
        dest="config",
        type=str,
        required=True,
        help="path to all configs file",
    )
    parser.add_argument(
        "--mode",
        action="store",
        dest="mode",
        type=str,
        required=False,
        help="mode of implementation ['igraph', 'nx', 'infosys']",
    )
    parser.add_argument(
        "--times",
        action="store",
        dest="times",
        type=str,
        required=False,
        help="Number of times to run simulation",
    )
    parser.add_argument(
        "--nthreads",
        action="store",
        dest="nthreads",
        type=str,
        required=False,
        help="Number of threads (ThreadPoolExecutor max_workers) to run simulation",
    )

    args = parser.parse_args(args)
    infile = args.infile
    outfile = args.outfile
    reshare_fpath = (
        args.resharefpath if args.resharefpath is not None else "reshares.csv"
    )
    verboseout = args.verboseoutfile
    configfile = args.config
    n_simulations = args.times

    infosys_spec = json.load(open(configfile, "r"))
    infosys_spec["graph_gml"] = infile
    infosys_spec["mode"] = args.mode if args.mode is not None else "igraph"
    if args.nthreads is not None:
        infosys_spec["n_threads"] = int(args.nthreads)

    # avoid passing undefined keyword to InfoSys
    legal_specs = utils.remove_illegal_kwargs(infosys_spec, SimSom.__init__)

    nruns_measurements = multiple_simulations(
        legal_specs,
        times=int(n_simulations),
        reshare_fpath=reshare_fpath,
        verboseout=verboseout,
    )
    # add infosys configuration
    infosys_spec.update(nruns_measurements)

    # save even empty results so smk don't complain
    fout = open(outfile, "w")
    json.dump(infosys_spec, fout)
    fout.flush()
    fout.close()


if __name__ == "__main__":
    main(sys.argv[1:])
