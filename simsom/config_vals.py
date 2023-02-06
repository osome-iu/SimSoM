import numpy as np

follower_network = "follower_network.gml"
mode = "igraph"

##### DEFAULT VALUES #####
DEFAULT_PHI = 0
DEFAULT_THETA = 1
DEFAULT_BETA = 0.05
DEFAULT_GAMMA = 0.01
DEFAULT_STRATEGY = None
DEFAULT_RHO = 0.8
DEFAULT_EPSILON = 0.0001
DEFAULT_MU = 0.5
DEFAULT_ALPHA = 15

##### EXPLORE COGNITIVE PARAMS #####
MU_SWIPE = [0.1, 0.25, 0.5, 0.75, 0.9]
ALPHA_SWIPE = [1, 2, 4, 8, 16, 32, 64, 128]

##### NETWORK INITIALIZATION (WITH BOTS) #####
TARGETING = [None, "hubs", "partisanship", "conservative", "liberal", "misinformation"]
GAMMA = sorted(list(10.0 ** (np.arange(-4, 0))))

##### EXPLORE OTHER BOT PARAMS #####
THETA_SWIPE = [1, 2, 4, 8, 16, 32, 64]
PHI_SWIPE = list(np.arange(0, 1.1, 0.1))

infosys_default = {
    "verbose": False,
    "output_cascades": True,
    "epsilon": DEFAULT_EPSILON,
    "rho": DEFAULT_RHO,
    "mu": DEFAULT_MU,
    "phi": DEFAULT_PHI,
    "alpha": DEFAULT_ALPHA,
    "theta": DEFAULT_THETA,
}

default_net = {
    "beta": DEFAULT_BETA,
    "gamma": DEFAULT_GAMMA,
    "targeting_criterion": None,
    "verbose": False,
    "human_network": follower_network,
}

baseline_exp = {
    "beta": 0,
    "targeting_criterion": DEFAULT_STRATEGY,
    "gamma": 0,
    "verbose": False,
    "output_cascades": False,
    "human_network": follower_network,
    "epsilon": DEFAULT_EPSILON,
    "rho": DEFAULT_RHO,
    "mu": DEFAULT_MU,
    "phi": DEFAULT_PHI,
    "alpha": DEFAULT_ALPHA,
    "theta": DEFAULT_THETA,
}

extreme_exp = {
    "beta": DEFAULT_BETA,
    "targeting_criterion": DEFAULT_STRATEGY,
    "gamma": GAMMA[-1],
    "verbose": False,
    "human_network": follower_network,
    "epsilon": DEFAULT_EPSILON,
    "rho": DEFAULT_RHO,
    "mu": DEFAULT_MU,
    "alpha": DEFAULT_ALPHA,
    "phi": PHI_SWIPE[-1],
    "theta": THETA_SWIPE[-1],
}
