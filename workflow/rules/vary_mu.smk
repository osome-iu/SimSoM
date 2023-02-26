import simsom.utils as utils

ABS_PATH = '/N/slate/baotruon/simsom_data'
DATA_PATH = os.path.join(ABS_PATH, "data")
CONFIG_PATH = os.path.join(ABS_PATH, "config_02172023")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = "vary_mu"
baseline_expname="baseline"
EXPS = json.load(open(config_fname,'r'))[exp_type]

sim_num = 2
mode='igraph'

RES_DIR = os.path.join(ABS_PATH,'results', 'short', f'02262023_{exp_type}_{sim_num}runs')
# TRACKING_DIR = os.path.join(ABS_PATH,'results', 'verbose', f'{exp_type}_{sim_num}runs')

rule all:
    input: 
        expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=list(EXPS.keys())),

rule run_simulation:
    input: 
        network = ancient(os.path.join(DATA_PATH, mode, f"network_{baseline_expname}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json"))
    output: 
        measurements = os.path.join(RES_DIR, '{exp_no}.json'),
        # tracking = os.path.join(TRACKING_DIR, '{exp_no}.json.gz')
    shell: """
        python3 -m workflow.scripts.driver -i {input.network} -o {output.measurements} --config {input.configfile} --mode {mode} --times {sim_num}
    """

rule init_net:
    input: 
        follower=os.path.join(DATA_PATH, 'follower_network.gml'),
        configfile = os.path.join(CONFIG_PATH, baseline_expname, f"{baseline_expname}.json")
        
    output: os.path.join(DATA_PATH, mode, f"network_{baseline_expname}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile} --mode {mode}
        """ 