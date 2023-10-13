Create a small network to replicate results from v.2 
- Filter out a subgraph containing nodes with partisanship info 
- k-core decomposition until ~ 1k nodes in core

Nodes that have partisanship info:  15056
58048 nodes and 10499218 edges initially(average number of friends: 180.87131339581038)
15056 nodes and 4327448 edges after filtering
939-core has 1040 nodes, 700896 edges
939-core after edge-sampling has 1040 nodes, 188106 edges, and average number of friends 180.87115384615385

Infosys network specs: 
net_specs = {
    "targeting_criterion": None,
    "human_network": None,
    "n_humans": 1000,
    "beta": 0.05,  # 50 bot
    "gamma": 0.01,  # each has 10 followers
    "verbose": True,
}
