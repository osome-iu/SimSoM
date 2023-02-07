import simsom.utils as utils
import simsom.config_vals as configs

ABS_PATH = '/N/slate/baotruon/simsom_data'
DATA_PATH = os.path.join(ABS_PATH, "data")
CONFIG_PATH = os.path.join(ABS_PATH, "config")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = "vary_gamma_notracking"
# get network names corresponding to the strategy
EXPS = json.load(open(config_fname,'r'))[exp_type]

gamma_jdxs = [str(configs.GAMMA.index(gamma)) for gamma in [0.001, 0.01]]
target = [None]
EXP_NOS = [
        exp_name
        for exp_name in EXPS.keys()
        if 'None' in exp_name and exp_name.endswith(tuple(gamma_jdxs))
    ]

EXP2NET = {exp_name: utils.netconfig2netname(config_fname, net_cf) for exp_name, net_cf in EXPS.items() if exp_name in EXP_NOS}
sim_num = 3
mode='igraph'

RES_DIR = os.path.join(ABS_PATH,'results', 'short', f'02062023_{exp_type}_{sim_num}runs')
TRACKING_DIR = os.path.join(ABS_PATH,'results', 'verbose', f'02062023_{exp_type}_{sim_num}runs')

rule all:
    input: 
        expand(os.path.join(RES_DIR, '{exp_no}.json'), exp_no=EXP_NOS),

rule run_simulation:
    input: 
        network = ancient(lambda wildcards: os.path.join(DATA_PATH, mode, 'vary_network', f"network_{EXP2NET[wildcards.exp_no]}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, exp_type, "{exp_no}.json"))
    output: 
        measurements = os.path.join(RES_DIR, '{exp_no}.json'),
        tracking = os.path.join(TRACKING_DIR, '{exp_no}.json.gz')
    shell: """
        python3 -m workflow.scripts.driver -i {input.network} -o {output.measurements} -v {output.tracking} --config {input.configfile} --mode {mode} --times {sim_num}
    """

rule init_net:
    input: 
        follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
        configfile = ancient(os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json"))
        
    output: os.path.join(DATA_PATH, mode, 'vary_network', "network_{net_no}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile} --mode {mode}
        """ 