""" 
    Make exp config 
    - Exps on Human characteristics
        - baseline
        - varymu, varyalpha: No targeting strategy, default values for the rest of the parameters
        - shuffe: {community-preserved , hub-preserved}
    - Bot tactics: explore single variable & combinatory effects:
        - thetaphi
        - phigamma
        - thetagamma
    - Targeting strategies
        - Default values, only change targeting 
"""
import simsom.utils as utils
import simsom.config_vals as configs
import os
import json


def save_config_to_subdir(config, config_name, saving_dir, exp_type):
    """
    Save each exp to a .json file 
    """
    output_dir = os.path.join(saving_dir, f"{exp_type}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    json.dump(config, open(os.path.join(output_dir, f"{config_name}.json"), "w"))


def make_exps(saving_dir, default_net_config, default_infosys_config):
    """
    Create configs for exps
    Outputs:
        - a master file (.json) for all configs
        - an experiment config (.json) save to a separate directory `{saving_dir}/{exp_type}/{config_id}.json`
    """
    all_exps = {}

    ##### NETWORK INITIALIZATION (WITH BOTS) #####
    ##### Networks created are used commonly across all gamma values (we don't have to re-generate network for each simulation)
    all_exps["vary_network"] = {}

    for jdx, gamma in enumerate(configs.GAMMA):
        for kdx, target in enumerate(configs.TARGETING):
            cf = {
                "beta": configs.DEFAULT_BETA,
                "gamma": gamma,
                "targeting_criterion": target,
            }
            config = utils.update_dict(cf, default_net_config)
            config = utils.update_dict(config, default_infosys_config)

            config_name = f"{jdx}{kdx}"
            all_exps["vary_network"][config_name] = config

            save_config_to_subdir(config, config_name, saving_dir, "vary_network")

    assert len(all_exps["vary_network"]) == len(configs.GAMMA) * len(configs.TARGETING)

    ##### BASELINE #####
    all_exps["baseline"] = {}
    config_name = f"baseline"
    config = configs.baseline_exp
    all_exps["baseline"][config_name] = config

    save_config_to_subdir(config, config_name, saving_dir, "baseline")

    ##### EXTREME BOT ACTIVITY #####
    all_exps["extreme"] = {}
    # exp with highest bot paramters (gamma, theta, phi)
    # 2 last values of theta (depending on what we decide to include in the paper)
    for idx, theta in enumerate(configs.THETA_SWIPE[-2:]):
        cf = {"theta": theta}
        config = utils.update_dict(cf, configs.extreme_exp)
        config_name = f"extreme{idx}"
        all_exps["extreme"][config_name] = config
        save_config_to_subdir(config, config_name, saving_dir, "extreme")

    ##### EXPLORE COGNITIVE PARAMS #####
    all_exps["vary_mu"] = {}
    for idx, mu in enumerate(configs.MU_SWIPE):
        for kdx, target in enumerate([configs.DEFAULT_STRATEGY]):
            cf = {"mu": mu, "targeting_criterion": target}

            config = utils.update_dict(cf, default_net_config)
            config = utils.update_dict(config, default_infosys_config)

            config_name = f"{str(target)}{idx}"
            all_exps["vary_mu"][config_name] = config

            save_config_to_subdir(config, config_name, saving_dir, "vary_mu")

    all_exps["vary_alpha"] = {}
    for idx, alpha in enumerate(configs.ALPHA_SWIPE):
        for kdx, target in enumerate([configs.DEFAULT_STRATEGY]):
            cf = {"alpha": alpha, "targeting_criterion": target}

            config = utils.update_dict(cf, default_net_config)
            config = utils.update_dict(config, default_infosys_config)

            config_name = f"{str(target)}{idx}"
            all_exps["vary_alpha"][config_name] = config

            save_config_to_subdir(config, config_name, saving_dir, "vary_alpha")

    ##### EXPLORE BOT PARAMS #####
    all_exps["vary_thetaphi"] = {}
    for idx, theta in enumerate(configs.THETA_SWIPE):
        for jdx, phi in enumerate(configs.PHI_SWIPE):
            cf = {"theta": theta, "phi": phi}
            config = utils.update_dict(cf, default_net_config)
            config = utils.update_dict(config, default_infosys_config)

            config_name = f"{idx}{jdx}"
            all_exps["vary_thetaphi"][config_name] = config

            save_config_to_subdir(config, config_name, saving_dir, "vary_thetaphi")

    all_exps["vary_thetagamma"] = {}
    for idx, theta in enumerate(configs.THETA_SWIPE):
        for jdx, gamma in enumerate(configs.GAMMA):
            cf = {"theta": theta, "gamma": gamma}
            config = utils.update_dict(cf, default_net_config)
            config = utils.update_dict(config, default_infosys_config)

            config_name = f"{idx}{jdx}"
            all_exps["vary_thetagamma"][config_name] = config

            save_config_to_subdir(config, config_name, saving_dir, "vary_thetagamma")

    all_exps["vary_phigamma"] = {}
    for idx, phi in enumerate(configs.PHI_SWIPE):
        for jdx, gamma in enumerate(configs.GAMMA):
            cf = {"phi": phi, "gamma": gamma}
            config = utils.update_dict(cf, default_net_config)
            config = utils.update_dict(config, default_infosys_config)

            config_name = f"{idx}{jdx}"
            all_exps["vary_phigamma"][config_name] = config

            save_config_to_subdir(config, config_name, saving_dir, "vary_phigamma")

    ##### EXPLORE BOT TARGETING STRATEGIES #####
    # Vary single variable for each targeting strategy
    all_exps["vary_gamma"] = {}
    for idx, gamma in enumerate(configs.GAMMA):
        for kdx, target in enumerate(configs.TARGETING):
            cf = {"gamma": gamma, "targeting_criterion": target}

            config = utils.update_dict(cf, default_net_config)
            config = utils.update_dict(config, default_infosys_config)

            config_name = f"{str(target)}{idx}"
            all_exps["vary_gamma"][config_name] = config
            save_config_to_subdir(config, config_name, saving_dir, "vary_gamma")

    fp = os.path.join(saving_dir, "all_configs.json")
    json.dump(all_exps, open(fp, "w"))
    print(f"Finish saving config to {fp}")


if __name__ == "__main__":
    ABS_PATH = "exps"

    # ABS_PATH = "/N/slate/baotruon/marketplace"

    saving_dir = os.path.join(ABS_PATH, "config")
    make_exps(saving_dir, configs.default_net, configs.infosys_default)
