"""
Snakefile to run experiments with varying theta and gamma values
(Total 28 jobs)
"""

import json 
import simsom.utils as utils

ABS_PATH = '/N/project/simsom/simsom_v3'
DATA_PATH = "/N/slate/baotruon/simsom_data/data"
CONFIG_PATH = os.path.join(ABS_PATH, "config_ouput_cascade_false")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = 'vary_thetagamma'

# get names for exp_config and network
EXPS = json.load(open(config_fname,'r'))[exp_type]
EXP_NOS = list(EXPS.keys())
EXP2NET = {
    exp_name: utils.netconfig2netname(config_fname, net_cf)
    for exp_name, net_cf in EXPS.items()
}

nthreads=21
sim_num = 6
mode='igraph'

RES_DIR = os.path.join(ABS_PATH,'results_bigred', f'{exp_type}_6runs')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose_bigred', f'{exp_type}_6runs')
# CASCADE_DIR = os.path.join(ABS_PATH,'results_cascade', f'{exp_type}')

rule all:
    input: 
        results = expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=EXP_NOS)

rule run_simulation:
    input: 
        network = ancient(lambda wildcards: os.path.join(DATA_PATH, mode, 'vary_network', f"network_{EXP2NET[wildcards.exp_no]}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json")) #data/vary_thetabeta/004.json
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