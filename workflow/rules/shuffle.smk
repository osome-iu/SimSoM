"""
Snakefile to run experiments using different shuffled version of the default network (gamma=0.01)
"""

import json 
import simsom.utils as utils

ABS_PATH = '/N/project/simsom/simsom_v3/v3.3_full'
DATA_PATH = "/N/project/simsom/simsom_v3/v3.3_full/data"

# ABS_PATH = 'experiments'
# DATA_PATH = os.path.join(ABS_PATH, "data")

# `shuffle` uses .json configs copied from vary_gamma/*{[0,1,2,3]}.json (where gamma=0.0001, 0.001, 0.01 and 0.1)
CONFIG_PATH = os.path.join(ABS_PATH, "config")
config_fname = os.path.join(CONFIG_PATH, 'all_configs.json')

# EXP_NOS = ['conservative', 'liberal', 'hubs', 'None']
# GAMMAS = [0,1,2,3] # [0.0001, 0.001, 0.01, 0.1]

EXP_NOS = ['None']
GAMMAS = [2,3] # only run for default gamma=0.01
SHUFFLES = ['hub','community', 'all']

nthreads = 7
mode='igraph'
sim_num=5

RES_DIR = os.path.join(ABS_PATH,'results', f'shuffle_5runs')
TRACKING_DIR = os.path.join(ABS_PATH,'results_verbose', f'shuffle_5runs')

rule all:
    input: 
        expand(os.path.join(RES_DIR, '{shuffle}_shuffle__{strategy}{gamma}.json'), shuffle=SHUFFLES, strategy=EXP_NOS, gamma=GAMMAS),


rule run_simulation:
    input: 
        network = ancient(os.path.join(DATA_PATH, 'shuffle_infosysnet', "{shuffle}_shuffle__{strategy}{gamma}.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, 'shuffle', '{strategy}{gamma}.json'))
    output: 
        measurements = os.path.join(RES_DIR, '{shuffle}_shuffle__{strategy}{gamma}.json'),
        tracking = os.path.join(TRACKING_DIR, '{shuffle}_shuffle__{strategy}{gamma}.json.gz')
    threads: nthreads
    shell: """
        python3 -m workflow.scripts.driver -i {input.network} -o {output.measurements} -v {output.tracking} --config {input.configfile} --times {sim_num} --nthreads {nthreads}
    """


rule init_net:
    input: 
        follower = ancient(os.path.join(DATA_PATH, 'shuffle_network', "network_{shuffle}_10iter.gml")),
        configfile = ancient(os.path.join(CONFIG_PATH, 'shuffle', '{strategy}{gamma}.json'))
        
    output: os.path.join(DATA_PATH, 'shuffle_infosysnet', "{shuffle}_shuffle__{strategy}{gamma}.gml")

    shell: """
            python3 -m workflow.scripts.init_net -i {input.follower} -o {output} --config {input.configfile}
        """ 


rule shuffle_net:
    input:  follower=ancient(os.path.join(DATA_PATH, 'follower_network.gml')),
    output: os.path.join(DATA_PATH, 'shuffle_network', "network_{shuffle}_10iter.gml")
    shell: """
        python3 -m workflow.scripts.shuffle_net -i {input} -o {output} --mode {wildcards.shuffle} --iter 10
    """ 