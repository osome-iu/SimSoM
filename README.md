# Vulnerabilities of the Online Public Square to Manipulation

This repository contains code to reproduce the results in the paper [*Vulnerabilities of the Online Public Square to Manipulation*](https://arxiv.org/abs/1907.06130) by Bao Tran Truong, Xiaodan Lou, Alessandro Flammini, and [Filippo Menczer](https://cnets.indiana.edu/fil/).

## Data
Network is created from the [Replication Data for: Right and left, partisanship predicts vulnerability to misinformation](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/6CZHH5)
Where: 
- `measures.tab` contains user information, i.e., one's partisanship and misinformation score. 
- `anonymized-friends.json` is the adjacency list. 

[Script to create network](workflow/make_network.py)

## Environment

Our code is based on **Python3.6+**, with **jupyter notebook**.

## Notes

The results in the paper are based on averages across multiple simulation runs. To reproduce those results, we suggest running the simulations in parallel, for example on a cluster, since they will need a lot of memory and CPU time.

## Notes on revised code:
Activate virtualenv and run `pip install -e .` for the module imports to work correctly.

Run minimal example with `workflow/example/run_simulation.py`

How to multiple experiments:
- run `workflow/scripts/make_finalconfig.py` (this creates config files for different sets of param combination you want to test)
- run `workflow/final_rules/<exp_type>.smk` (exp_type: [strategies_beta, vary_thetabeta, etc.])