""" Script to run simulations """

from infosys.InfoSys import InfoSystem
import infosys.utils as utils

import gzip
import sys
import argparse
import json
import numpy as np
import copy
from collections import defaultdict
import os


def multiple_simulations(infosys_specs, times=1, reshare_fpath="reshares.csv"):
    # baseline:  mu=0.5, alpha=15, beta=0.01, gamma=0.001, phi=1, theta=1
    # cascade data file name has format: f"{basedir}{exp_name}__{cascade_type}_{run_no}.csv"
    metrics = ["quality", "diversity", "discriminative_pow"]
    n_measures = defaultdict(lambda: [])

    print(f"Run simulation {times} times..")
    for time in range(times):

        try:
            print("Create InfoSystem instance..")
            follower_sys = InfoSystem(**infosys_specs)
            print("Start simulation ..")
            dir = os.path.dirname(reshare_fpath)
            exp_name = os.path.basename(reshare_fpath).split("__")[0]
            #  make a reshare.csv file no matter what. Save to other files according to number of (multiple) runs.
            if time > 0:
                prefix = f"_{time}.csv"
            else:
                prefix = f".csv"
            measurements = follower_sys.simulation(
                reshare_fpath=reshare_fpath.replace(".csv", prefix),
                exposure_fpath=os.path.join(dir, f"{exp_name}__exposure{prefix}"),
                activation_fpath=os.path.join(dir, f"{exp_name}__activation{prefix}"),
            )

            # Update results over multiple simulations
            for k, val in measurements.items():
                n_measures[k] += [val]

        except Exception as e:
            print("Error creating InfoSystem instance of running simulation.")
            print(e)

    print(
        f"average quality for follower network: {np.mean(np.array(n_measures['quality']))} pm {np.std(np.array(n_measures['quality']))}"
    )

    results = {metric: n_measures[metric] for metric in metrics}

    # return a short & long (more details) version of measurements
    return results, dict(n_measures)


def run_simulation(infosys_specs, reshare_fpath="reshares.csv"):
    # baseline:  mu=0.5, alpha=15, beta=0.01, gamma=0.001, phi=1, theta=1
    print("Create InfoSystem instance..")
    follower_sys = InfoSystem(**infosys_specs)
    print(f"Start simulation..")
    dir = os.path.dirname(reshare_fpath)
    exp_name = os.path.basename(reshare_fpath).split("__")[0]
    measurements = follower_sys.simulation(
        reshare_fpath=reshare_fpath,
        exposure_fpath=os.path.join(dir, f"{exp_name}", "__exposure.csv"),
        activation_fpath=os.path.join(dir, f"{exp_name}", "__activation.csv"),
    )
    print("average quality for follower network:", measurements["quality"])
    return measurements


def main(args):
    # TODO: remove mode
    parser = argparse.ArgumentParser(
        description="run simulation on an igraph instance of InfoSystem",
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
    # parser.add_argument(
    #     "-e",
    #     "--exposurefpath",
    #     action="store",
    #     dest="exposurefpath",
    #     type=str,
    #     required=False,
    #     help="path to .csv file containing exposure cascade info",
    # )
    # parser.add_argument(
    #     "-a",
    #     "--activationfpath",
    #     action="store",
    #     dest="activationfpath",
    #     type=str,
    #     required=False,
    #     help="path to .csv file containing agent activation info",
    # )

    parser.add_argument(
        "-v",
        "--verboseoutfile",
        action="store",
        dest="verboseoutfile",
        type=str,
        required=False,
        help="path to .json.gz file containing verbose infosys measurements (track all memes & feeds)",
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
        required=True,
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

    args = parser.parse_args(args)
    infile = args.infile
    outfile = args.outfile
    reshare_fpath = args.resharefpath
    # exposure_fpath = args.exposurefpath
    # activation_fpath = args.activationfpath
    verboseout = args.verboseoutfile
    configfile = args.config
    n_simulations = args.times
    infosys_spec = json.load(open(configfile, "r"))

    # graph_file = os.path.join(indir, infosys_spec['graph_gml'])
    infosys_spec["graph_gml"] = infile
    infosys_spec["mode"] = args.mode

    # avoid passing undefined keyword to InfoSys
    legal_specs = utils.remove_illegal_kwargs(infosys_spec, InfoSystem.__init__)

    nruns_measurements, verbose_tracking = multiple_simulations(
        legal_specs,
        times=int(n_simulations),
        reshare_fpath=reshare_fpath,
        # exposure_fpath=exposure_fpath,
        # activation_fpath=activation_fpath,
    )
    # add infosys configuration
    infosys_spec.update(nruns_measurements)

    # save even empty results so smk don't complain
    fout = open(outfile, "w")
    json.dump(infosys_spec, fout)
    fout.flush()

    if verboseout is not None:
        specs = copy.deepcopy(infosys_spec)
        specs.update(verbose_tracking)
        fout = gzip.open(verboseout, "w")
        utils.write_json_compressed(fout, specs)
        # force writing out the changes
        fout.flush()


if __name__ == "__main__":
    main(sys.argv[1:])

