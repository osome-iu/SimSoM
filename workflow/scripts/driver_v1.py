""" Script to run simulation(s)
    Parse command-line arguments specifying simulation parameters and output file paths 
    Run simulation(s)

    Reshare output file (.csv) and verbose tracking file (.json.gz) names are always suffixed by number of runs 
    e.g: if no_run=1, reshare_fpath="reshares_0.csv" and verboseout="verboseout_0.json.gz"
"""

from simsom import SimSomA1
import simsom.utils as utils
import sys
import argparse
import json
import numpy as np
import copy
from collections import defaultdict
import os
from datetime import datetime


def multiple_simulations(
    infosys_specs,
    logger,
    times=1,
    reshare_fpath="reshares.csv",
    verboseout=None,
):
    # baseline:  mu=0.5, sigma=15, beta=0.01, gamma=0.001, phi=1, theta=1
    # cascade data file name has format: f"{basedir}{exp_name}__{cascade_type}_{run_no}.csv"
    metrics = ["quality", "diversity", "discriminative_pow"]
    n_measures = defaultdict(lambda: [])

    logger.info(f"Run simulation {times} times..")
    for time in range(times):
        logger.info(f"**{time+1}/{times}**")
        try:
            logger.info("Create SimSomA1 instance..")
            follower_sys = SimSomA1(**infosys_specs, logger=logger)
            logger.info("Start simulation ..")
            # Tracking cascade info, files named by no.run
            if infosys_specs["output_cascades"] is True:
                n_reshare_fpath = (
                    reshare_fpath.replace(".csv", f"_{time}.csv")
                    if time > 0
                    else reshare_fpath
                )
            else:
                n_reshare_fpath = reshare_fpath
            measurements = follower_sys.simulation(reshare_fpath=n_reshare_fpath)

        except Exception as e:
            raise Exception("Failed to run simulations.", e)

        try:
            # Save verbose results, files named by no.run
            if verboseout is not None:
                n_verboseout = (
                    verboseout.replace(".json.gz", f"_{time}.json.gz")
                    if time > 0
                    else verboseout
                )
                specs = copy.deepcopy(infosys_specs)
                specs.update(measurements)
                utils.write_json_compressed(n_verboseout, specs)

        except Exception as e:
            raise ("Error saving verbose results", e)

        # Update results over multiple simulations for summary statistics
        for metric in metrics:
            n_measures[metric] += [measurements[metric]]

    logger.info(
        f"average quality for follower network: %s pm %s",
        np.mean(np.array(n_measures["quality"])),
        np.std(np.array(n_measures["quality"])),
    )

    # return a short version of measurements
    return dict(n_measures)


def run_simulation(infosys_specs, logger, reshare_fpath="reshares.csv"):
    # baseline:  mu=0.5, sigma=15, beta=0.01, gamma=0.001, phi=1, theta=1
    logger.info("Create SimSom instance..")
    follower_sys = SimSomA1(**infosys_specs)
    logger.info(f"Start simulation..")
    measurements = follower_sys.simulation(reshare_fpath=reshare_fpath)
    logger.info("average quality for follower network:", measurements["quality"])
    return measurements


def main(args):
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
    verboseout = args.verboseoutfile
    reshare_default_path = f"{os.path.dirname(verboseout)}/cascades"
    reshare_fpath = (
        args.resharefpath
        if args.resharefpath is not None
        else f"{reshare_default_path}/{os.path.basename(outfile).replace('.json',f'.reshares.csv')}"
    )
    configfile = args.config
    n_simulations = args.times

    infosys_spec = json.load(open(configfile, "r"))
    infosys_spec["graph_gml"] = infile
    if args.nthreads is not None:
        infosys_spec["n_threads"] = int(args.nthreads)

    ## LOGGING
    log_dir = f"{os.path.dirname(outfile)}/logs"
    # Use formatted current date and time as logging file name
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d.%H%M%S")

    logger = utils.get_file_logger(
        log_dir=log_dir,
        full_log_path=os.path.join(
            log_dir,
            f"{os.path.basename(outfile).replace('.json',f'__{formatted_datetime}.log')}",
        ),
        also_print=True,
    )
    # avoid passing undefined keyword to InfoSys
    legal_specs = utils.remove_illegal_kwargs(infosys_spec, SimSomA1.__init__)

    logger.info("Finished parsing arguments. Running simulation.. ")

    nruns_measurements = multiple_simulations(
        legal_specs,
        logger=logger,
        times=int(n_simulations),
        reshare_fpath=reshare_fpath,
        verboseout=verboseout,
    )
    # add infosys configuration
    infosys_spec.update(nruns_measurements)

    logger.info("Saving short results.. ")
    # save even empty results so smk don't complain
    fout = open(outfile, "w")
    json.dump(infosys_spec, fout)
    fout.flush()
    fout.close()

    logger.info("Done!")


if __name__ == "__main__":
    main(sys.argv[1:])
