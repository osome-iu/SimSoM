# SimSoM: A Simulator of Social Media

This repository contains code to reproduce the results in the paper [*Vulnerabilities of the Online Public Square to Manipulation*](https://arxiv.org/abs/1907.06130) by [Bao Tran Truong](https://btrantruong.github.io/), Xiaodan Lou, [Alessandro Flammini](https://cnets.indiana.edu/aflammin/), and [Filippo Menczer](https://cnets.indiana.edu/fil/).

## Overview of the repo
1. `data`: contains raw & derived datasets
2. `example`: contains a minimal example to start using the SimSoM model
3. `simsom`: the package for the SimSoM model that can be imported into scripts
4. `results`: .ipynb noteboooks to produce figures reported in the paper
5. `workflow`: workflow files (Snakemake rules) and scripts

## Environment set-up
- This code is written and tested with **Python>=3.6** 
- Run `conda env create -n simsom -f environment.yml` to create the environment with required packages
- Activate virtualenv and run `pip install -e .` for the module imports to work correctly.

## Data
The empirical network is created from the [Replication Data](https://doi.org/10.7910/DVN/6CZHH5) for: [Right and left, partisanship predicts vulnerability to misinformation](https://doi.org/10.37016/mr-2020-55),
where: 
- `measures.tab` contains user information, i.e., one's partisanship and misinformation score. 
- `anonymized-friends.json` is the adjacency list. 

We reconstruct the empirical network from the above 2 files, resulting in `data/follower_network.gml`. The steps are specified in the [script to create empirical network](workflow/make_network.py)

## Running the code

Run a minimal example using `workflow/example/run_simulation.py`

### Reproduce results from the paper:
1. From the root directory, unzip the data file using `unzip data/data.zip -d .`
2. Create config files specifying parameters for simulations. 
    - How? run `workflow/scripts/make_finalconfig.py`
    - See `example/data/config.json` for example of a config file
3. Run a Snakemake rule corresponding to the simulations of interest. 
    e.g.: `workflow/rules/shuffle_network.smk` runs simulations on different shuffled version of the empirical network

### Notes
The results in the paper are based on averages across multiple simulation runs. To reproduce those results, we suggest running the simulations in parallel, for example on a cluster, since they will need a lot of memory and CPU time.
