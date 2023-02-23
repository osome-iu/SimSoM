This directory contains the scripts and Snakemake rules to run simulations whose results are reported in the paper.

# Scripts:
The `scripts` directory contains the scripts needed for the simulation:
- `driver.py`: script to run simulations
- `init_net.py`: script to initialize Information network based on a .json configuration file that specifies the bot parameters ($\gamma, \beta$, bot targeting strategies)
- `make_config.py`: specifying parameters for sets of experiments  
- `make_network.py`: create the empirical follower network as input to simulations.
 1. Reconstruct the follower network for data files provided in [Nikolov et al.'s paper](doi.org/10.7910/DVN/6CZHH5)
 2. Further filter to make the network more manageable 
- `shuffle_net.py`: script to shuffle the network 

# Snakemake rules
The `rules` directory contains Snakemake rules to produce results that are reported in the paper. 

Snakemake is a powerful workflow that helps keeping track of experiments systematically. Each Snakemake file consists of rules that define how to create output files from input files. Dependencies between the rules are determined automatically, creating a DAG (directed acyclic graph) of jobs that can be automatically parallelized. Read more about Snakemake in its [documentation](https://snakemake.readthedocs.io/en/v5.1.4/executable.html)
- Each rule runs a set of simulations corresponding to an analysis. (The associated section and figure in the paper are listed with each rule, see more in `rules/README.md`)  

## How to run 
- Changing into the root directory of this project 
- First create the configuration for the desired experiments by calling `python3 workflow/scripts/make_config.py`. This will result in the `experiments/config` folder
- Run `snakemake --snakefile workflow/rules/<rule-name>.smk --cores all` where <rule-name> is the name of the Snakemake rule you want to run. 
