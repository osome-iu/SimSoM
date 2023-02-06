import simsom.utils as utils
import simsom.config_vals as configs

ABS_PATH = '/N/slate/baotruon/simsom_data'
DATA_PATH = os.path.join(ABS_PATH, "data")
CONFIG_PATH = os.path.join(ABS_PATH, "config")

config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')
exp_type = "vary_network"
# get network names corresponding to the strategy
EXPS = json.load(open(config_fname,'r'))[exp_type]
# only init networks of interest: 
gamma_jdxs = [configs.GAMMA.index(gamma) for gamma in [0.001, 0.01]]
target_idxs = [configs.TARGETING.index(target) for target in [None]]
EXP_NOS = list(
    [
        netname
        for netname in EXPS.keys()
        if int(netname[0]) in gamma_jdxs and int(netname[1]) in target_idxs
    ]
)
mode='igraph'

rule all:
    input:
        expand(os.path.join(DATA_PATH, mode, 'vary_network', "network_{net_no}.gml"), net_no=EXP_NOS)

rule init_net:
    input: 
        follower=os.path.join(DATA_PATH, 'follower_network.gml'),
        configfile = os.path.join(CONFIG_PATH, 'vary_network', "{net_no}.json")
        
    output: os.path.join(DATA_PATH, mode, 'vary_network', "network_{net_no}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile} --mode {mode}
        """ 