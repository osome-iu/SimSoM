"""
Snakefile to run experiments with varying alpha values (using a network with no bots)
"""

import json 
import simsom.utils as utils

ABS_PATH = '/N/project/simsom/simsom_v3/v3.0_10222023'
DATA_PATH = "/N/project/simsom/simsom_v3/v3.0_10222023/data"

# ABS_PATH = '/Users/baott/SimSoM/experiments/10172023_v3.0_exps'
# DATA_PATH = "/Users/baott/SimSoM/experiments/10172023_v3.0_exps/data"

CONFIG_PATH = os.path.join(ABS_PATH, "config")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = "vary_alpha"
# get network names corresponding to the strategy
EXPS = json.load(open(config_fname,'r'))[exp_type]

EXP_NOS = list(EXPS.keys())

nthreads=7
sim_num = 3
mode='igraph'

RES_DIR = os.path.join(ABS_PATH,'results', f'{exp_type}_3runs')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose', f'{exp_type}_3runs')

rule all:
    input: 
        expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=EXP_NOS),

rule run_simulation:
    input: 
        network = ancient(os.path.join(DATA_PATH, "network_baseline.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json"))
    output: 
        measurements = os.path.join(RES_DIR, '{exp_no}.json'),
        tracking = os.path.join(TRACKING_DIR, '{exp_no}.json.gz')
    threads: 7
    shell: """
        python3 -m workflow.scripts.driver -i {input.network} -o {output.measurements} -v {output.tracking} --config {input.configfile} --times {sim_num} --nthreads {nthreads}
    """

# rule init_net:
#     input: 
#         follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
#         configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
#     output: os.path.join(DATA_PATH, 'vary_network', "network_{net_no}.gml")

#     shell: """
#             python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
#         """ 