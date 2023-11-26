"""
Snakefile to run experiments with varying theta and phi values
cascade=True
maxtheta=32
"""

import json 
import simsom.utils as utils

ABS_PATH = '/N/project/simsom/simsom_v3/zl2_11252023'
DATA_PATH = "/N/project/simsom/simsom_v3/v3.3_10222023/data"
CONFIG_PATH = "/N/project/simsom/simsom_v3/v3.3_10222023/config_cascade_true"

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = 'vary_thetaphi'

# get names for exp_config and network
EXPS = json.load(open(config_fname,'r'))[exp_type]

MAXTHETA_IDX = 2  # 2^5 = 32
EXP_NOS = [exp for exp in EXPS.keys() if int(exp[0]) > MAXTHETA_IDX]
EXP2NET = {
    exp_name: utils.netconfig2netname(config_fname, net_cf)
    for exp_name, net_cf in EXPS.items()
    if exp_name in EXP_NOS
}

nthreads= 7
sim_num = 1

RES_DIR = os.path.join(ABS_PATH,'results', f'{exp_type}_cascade')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose', f'{exp_type}_cascade')
CASCADE_DIR = os.path.join(ABS_PATH,'results_cascade', f'{exp_type}_cascade')

rule all:
    input: 
        expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=EXP_NOS),

rule run_simulation:
    input: 
        network = ancient(lambda wildcards: os.path.join(DATA_PATH, 'vary_network', f"network_{EXP2NET[wildcards.exp_no]}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json"))
    output: 
        measurements = os.path.join(RES_DIR, '{exp_no}.json'),
        tracking = os.path.join(TRACKING_DIR, '{exp_no}.json.gz'),
        reshare =  os.path.join(CASCADE_DIR, '{exp_no}__reshare.csv')
    threads: nthreads
    shell: """
        python3 -m workflow.scripts.driver_zl2 -i {input.network} -o {output.measurements} -r {output.reshare} -v {output.tracking} --config {input.configfile} --times {sim_num} --nthreads {nthreads}
    """

rule init_net:
    input: 
        follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, 'vary_network', "network_{net_no}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
        """ 