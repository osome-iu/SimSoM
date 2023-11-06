"""
Snakefile to run experiments with 2 gamma values (0.001, 0.01) while saving cascade and exposure networks 
"""

import simsom.config_vals as configs

import json 

ABS_PATH = '/N/project/simsom/simsom_v3/v4.3z_11062023'
DATA_PATH = "/N/project/simsom/simsom_v3/v3.3_10222023/data"

# ABS_PATH = 'experiments'
# DATA_PATH = os.path.join(ABS_PATH, "data")

CONFIG_PATH = os.path.join(ABS_PATH, "config_cascade_true")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = "vary_gamma"
# get network names corresponding to the strategy
EXPS = json.load(open(config_fname,'r'))[exp_type]
EXP_NOS = [
        exp_name
        for exp_name in EXPS.keys()
        if 'None' in exp_name and exp_name.endswith(configs.GAMMA.index(configs.DEFAULT_GAMMA))
    ]
EXP2NET = {exp_name: utils.netconfig2netname(config_fname, net_cf) for exp_name, net_cf in EXPS.items() if exp_name in EXP_NOS}

nthreads = 7
sim_num = 5

RES_DIR = os.path.join(ABS_PATH,'results', 'cascade_scaling')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose', 'cascade_scaling')
CASCADE_DIR = os.path.join(ABS_PATH,'results_cascade', 'cascade_scaling')

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
        python3 -m workflow.scripts.driver_43z -i {input.network} -o {output.measurements} -v {output.tracking} -r {output.reshare} --config {input.configfile} --times {sim_num} --nthreads {nthreads}
    """

rule init_net:
    input: 
        follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, 'vary_network', "network_{net_no}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
        """ 