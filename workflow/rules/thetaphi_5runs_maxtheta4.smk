"""
Snakefile to run experiments with varying theta and phi values
(Total 66)
"""

import json 
import simsom.utils as utils

# import simsom.config_vals as config_vals
# config_vals.THETA_SWIPE # [1, 2, 4, 8, 16, 32, 64]

ABS_PATH = '/N/project/simsom/simsom_v3'
DATA_PATH = "/N/slate/baotruon/simsom_data/data"
CONFIG_PATH = os.path.join(ABS_PATH, "config")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = 'vary_thetaphi'

# get names for exp_config and network
EXPS = json.load(open(config_fname,'r'))[exp_type]

MAXTHETA_IDX = 2  # 2^5 = 32
EXP_NOS = [exp for exp in EXPS.keys() if int(exp[0]) <= MAXTHETA_IDX]
EXP2NET = {
    exp_name: utils.netconfig2netname(config_fname, net_cf)
    for exp_name, net_cf in EXPS.items()
    if exp_name in EXP_NOS
}

nthreads=7
sim_num = 5
mode='igraph'

RES_DIR = os.path.join(ABS_PATH,'results_bigred', f'{exp_type}_5runs')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose_bigred', f'{exp_type}_5runs')
# CASCADE_DIR = os.path.join(ABS_PATH,'results_cascade', f'{exp_type}')

rule all:
    input: 
        expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=EXP_NOS),

rule run_simulation:
    input: 
        network = ancient(lambda wildcards: os.path.join(DATA_PATH, mode, 'vary_network', f"network_{EXP2NET[wildcards.exp_no]}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json"))
    output: 
        measurements = os.path.join(RES_DIR, '{exp_no}.json'),
        tracking = os.path.join(TRACKING_DIR, '{exp_no}.json.gz'),
        # reshare =  os.path.join(CASCADE_DIR, '{exp_no}__reshare.csv')
    threads: nthreads
    shell: """
        python3 -m workflow.scripts.driver -i {input.network} -o {output.measurements} -v {output.tracking} --config {input.configfile} --times {sim_num} --nthreads {nthreads}
    """

rule init_net:
    input: 
        follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, mode, 'vary_network', "network_{net_no}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
        """ 