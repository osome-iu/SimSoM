"""
Snakefile to run experiments with varying theta and gamma values
cascade=True
low infiltration (gamma=0.001), 4 values of theta
"""

import json 
import simsom.utils as utils
import simsom.config_vals as configs

ABS_PATH = '/N/project/simsom/simsom_v3/zl5_11252023'
DATA_PATH = "/N/project/simsom/simsom_v3/v3.3_10222023/data"
CONFIG_PATH = "/N/project/simsom/simsom_v3/v3.3_10222023/config_cascade_true"

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = 'vary_thetagamma'
GAMMA=['1', '2'] #index of gamma (0.001, 0.01)
# get names for exp_config and network
EXPS = json.load(open(config_fname,'r'))[exp_type]

THETA = configs.THETA_SWIPE
theta_vals = [1,4, 16, 64]
THETA_IDXS =[THETA.index(theta) for theta in theta_vals]

EXP_NOS = [exp for exp in EXPS.keys() if (exp[1] in GAMMA) and (int(exp[0]) in THETA_IDXS)]

EXP2NET = {
    exp_name: utils.netconfig2netname(config_fname, net_cf)
    for exp_name, net_cf in EXPS.items()
}

nthreads=7
sim_num = 1

RES_DIR = os.path.join(ABS_PATH,'results', f'{exp_type}_cascade_')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose', f'{exp_type}_cascade_')
CASCADE_DIR = os.path.join(ABS_PATH,'results_cascade', f'{exp_type}_cascade_')

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
        reshare =  os.path.join(CASCADE_DIR, '{exp_no}__reshare.csv')
    threads: nthreads
    shell: """
        python3 -m workflow.scripts.driver_zl5 -i {input.network} -o {output.measurements} -r {output.reshare} -v {output.tracking} --config {input.configfile} --times {sim_num} --nthreads {nthreads}
    """

rule init_net:
    input: 
        follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, 'vary_network', "network_{net_no}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
        """ 