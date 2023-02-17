import simsom.utils as utils

ABS_PATH = 'exps'
DATA_PATH = os.path.join(ABS_PATH, 'data')
CONFIG_PATH = os.path.join(ABS_PATH, "config_02172023")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = 'vary_phigamma'

# get names for exp_config and network
EXPS = json.load(open(config_fname,'r'))[exp_type]
EXP_NOS = list(EXPS.keys())
EXP2NET = {
    exp_name: utils.netconfig2netname(config_fname, net_cf)
    for exp_name, net_cf in EXPS.items()
}

sim_num = 3
mode='igraph'

RES_DIR = os.path.join(ABS_PATH,'results', 'short', f'02172023_{exp_type}_{sim_num}runs')
# TRACKING_DIR = os.path.join(ABS_PATH,'results', 'verbose', f'02172023_{exp_type}_{sim_num}runs')
# CASCADE_DIR = os.path.join(ABS_PATH,'results', 'cascade', f'02172023_{exp_type}_{sim_num}runs')

rule all:
    input: 
        results = expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=EXP_NOS)

rule run_simulation:
    input: 
        network = ancient(lambda wildcards: os.path.join(DATA_PATH, mode, 'vary_network', f"network_{EXP2NET[wildcards.exp_no]}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json")) #data/vary_thetabeta/004.json
    output: 
        measurements = os.path.join(RES_DIR, '{exp_no}.json'),
        # tracking = os.path.join(TRACKING_DIR, '{exp_no}.json.gz'),
        # reshare =  os.path.join(CASCADE_DIR, '{exp_no}__reshare.csv')
    shell: """
        python3 -m workflow.scripts.driver -i {input.network} -o {output.measurements}  --config {input.configfile} --mode {mode} --times {sim_num}
    """

rule init_net:
    input: 
        follower= ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, mode, 'vary_network', "network_{net_no}.gml")
    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile} --mode {mode}
        """ 