"""
Run exps with default bot and gamma value 
strategy='None', gamma=0.01, phi=0, theta=THETASWIPE
Use config & data from main v3.3 full exps 
cascade=False
"""

import json 
import simsom.utils as utils

ABS_PATH = '/N/project/simsom/simsom_v3/new_small/v2.1_10302023'
DATA_PATH = "/N/project/simsom/simsom_v3/10242023_v3.3/data"
CONFIG_PATH = "/N/project/simsom/simsom_v3/10242023_v3.3/config"

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = 'vary_thetaphi'
PHI='0' #index of phi=0

# get names for exp_config and network
EXPS = json.load(open(config_fname,'r'))[exp_type]
EXP_NOS = [exp for exp in EXPS.keys() if (exp[1]==PHI)]

EXP2NET = {
    exp_name: utils.netconfig2netname(config_fname, net_cf)
    for exp_name, net_cf in EXPS.items()
}

nthreads=7
sim_num = 5

RES_DIR = os.path.join(ABS_PATH,'results', f'{exp_type}_5runs')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose', f'{exp_type}_5runs')
# CASCADE_DIR = os.path.join(ABS_PATH,'results_cascade', f'{exp_type}')

rule all:
    input: 
        results = expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=EXP_NOS)

rule run_simulation:
    input: 
        network = ancient(lambda wildcards: os.path.join(DATA_PATH, 'vary_network', f"network_{EXP2NET[wildcards.exp_no]}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json")) #data/vary_thetabeta/004.json
    output: 
        measurements = os.path.join(RES_DIR, '{exp_no}.json'),
        tracking = os.path.join(TRACKING_DIR, '{exp_no}.json.gz'),
        # reshare =  os.path.join(CASCADE_DIR, '{exp_no}__reshare.csv')
    shell: """
        python3 -m workflow.scripts.driver_21 -i {input.network} -o {output.measurements} -v {output.tracking} --config {input.configfile} --times {sim_num}
    """

rule init_net:
    input: 
        follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, 'vary_network', "network_{net_no}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
        """ 