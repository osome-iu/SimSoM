"""
Utility functions to help with I/o, plotting and statistic tests
"""

import numpy as np
import sys
import logging
import os
import json
import gzip
import datetime as dt
import inspect
import scipy.stats as stats
import simsom.config_vals as configs

### I/O
def write_json_compressed(fout, data):
    # write compressed json for hpc - pass file handle instead of filename so we can flush
    try:
        fout.write(json.dumps(data).encode("utf-8"))
    except Exception as e:
        print(e)


def read_json_compressed(fpath):
    data = None
    try:
        fin = gzip.open(fpath, "r")
        json_bytes = fin.read()
        json_str = json_bytes.decode("utf-8")
        data = json.loads(json_str)
    except Exception as e:
        print(e)
    return data


### EXP CONFIGS
def update_dict(adict, default_dict, fill_na=True):
    # only update the dictionary if key doesn't exist
    # use to fill out the rest of the params we're not interested in
    # Fill NaN value if it exists in another dict

    for k, v in default_dict.items():
        if k not in adict.keys():
            adict.update({k: v})
        if fill_na is True and adict[k] is None:
            adict.update({k: v})
    return adict


def netconfig2netname(config_fname, network_config):
    # Map specific args to pre-constructed network name
    # network_config is a dict of at least 3 keys: {'gamma', 'strategy'}
    # structure: network_config = {'gamma':0.005, 'targeting_criterion': 'partisanship'}

    exp_configs = json.load(open(config_fname, "r"))
    EXPS = exp_configs[
        "vary_network"
    ]  # keys are name of network, format: '{betaidx}{gammaidx}{targetingidx}'

    legal_vals = ["gamma", "targeting_criterion"]
    network_config = {k: val for k, val in network_config.items() if k in legal_vals}

    GAMMA = configs.GAMMA
    TARGETING = configs.TARGETING

    network_fname = f"{GAMMA.index(network_config['gamma'])}{TARGETING.index(network_config['targeting_criterion'])}"

    for arg_name in network_config.keys():
        assert EXPS[network_fname][arg_name] == network_config[arg_name]

    return network_fname


def remove_illegal_kwargs(adict, amethod):
    # remove a keyword from a dict if it is not in the signature of a method
    new_dict = {}
    argspec = inspect.getargspec(amethod)
    legal = argspec.args
    for k, v in adict.items():
        if k in legal:
            new_dict[k] = v
    return new_dict


def get_now():
    # return timestamp
    return int(dt.datetime.now().timestamp())


def get_logger(name):
    # Create a custom logger
    logger = logging.getLogger(name)
    # Create handlers
    handler = logging.StreamHandler()
    # Create formatters and add it to handlers
    logger_format = logging.Formatter("%(asctime)s@%(name)s:%(levelname)s: %(message)s")
    handler.setFormatter(logger_format)
    # Add handlers to the logger
    logger.addHandler(handler)
    # Set level
    level = logging.getLevelName("INFO")
    logger.setLevel(level)
    return logger


def get_file_logger(log_dir=".log", also_print=False):
    """Create logger."""

    # Create log_dir if it doesn't exist already
    try:
        os.makedirs(f"{log_dir}")
    except:
        pass

    # Create logger and set level
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)

    # Configure file handler
    formatter = logging.Formatter(
        fmt="%(asctime)s-%(name)s-%(levelname)s-%(message)s",
        datefmt="%Y-%m-%d_%H:%M:%S",
    )
    log_fpath = os.path.join(log_dir, f"{__name__}_{get_now()}")
    fh = logging.FileHandler(log_fpath)
    fh.setFormatter(formatter)
    fh.setLevel(level=logging.INFO)
    # Add handlers to logger
    logger.addHandler(fh)

    # If true, also print the output to the console in addition to sending it to the log file
    if also_print:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        ch.setLevel(level=logging.INFO)
        logger.addHandler(ch)

    return logger


def safe_open(path, mode="w"):
    """ Open "path" for writing or reading, creating any parent directories as needed.
        mode =[w, wb, r, rb]
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, mode)


def kendall_tau(ranking1, ranking2):
    # ranking1: list of ranking for n elements in criteria1
    # ranking2: list of ranking for n elements in criteria2
    # such that ranking1[i] and ranking2[i] is the ranking of element i in 2 different criteria
    tau, p_value = stats.kendalltau(ranking1, ranking2)
    return tau, p_value


def entropy(x):
    # x: list of proportion
    entropy = np.sum(x * np.log(x))
    return entropy
