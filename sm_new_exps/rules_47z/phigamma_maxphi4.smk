"""
Snakefile to run experiments with varying phi and gamma values (except for gamma=0.01)
(Total 40 jobs)
Use network_*0.gml, where wildcards=[0,1,2,3] (for varying Gamma and None strategy)
"""

import simsom.utils as utils
import json 

ABS_PATH = '/N/project/simsom/simsom_v3/new_small/v4.7z_10302023'
DATA_PATH = "/N/project/simsom/simsom_v3/10242023_v3.3/data"
CONFIG_PATH = "/N/project/simsom/simsom_v3/10242023_v3.3/config"

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = 'vary_phigamma'

# get names for exp_config and network
GAMMA='2' #index of gamma (0.01)
EXPS = json.load(open(config_fname,'r'))[exp_type]

MAXPHI_IDX = 4  # 0.4

EXP_NOS = [exp for exp in EXPS.keys() if (exp[1]!=GAMMA) and (int(exp[0]) <= MAXPHI_IDX)]
EXP2NET = {
    exp_name: utils.netconfig2netname(config_fname, net_cf)
    for exp_name, net_cf in EXPS.items()
    if exp_name in EXP_NOS
}

nthreads=7
sim_num = 5
mode='igraph'

RES_DIR = os.path.join(ABS_PATH,'results', f'{exp_type}')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose', f'{exp_type}')
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
    threads: nthreads
    shell: """
        python3 -m workflow.scripts.driver_47z -i {input.network} -o {output.measurements} -v {output.tracking} --config {input.configfile} --times {sim_num} --nthreads {nthreads}
    """

rule init_net:
    input: 
        follower= ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, 'vary_network', "network_{net_no}.gml")
    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
        """ 