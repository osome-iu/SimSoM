""" Create the empirical follower network as input to simulations.
    1. Reconstruct the follower network for data files provided in doi.org/10.7910/DVN/6CZHH5
    2. Further filter to make the network more manageable 
    When filtering
        - make sure the degree of humans is comparable with degree of bots for the default gamma=0.01
        e.g: if degree of humans is 100, then degree of bots should be ~100, which is only possible with 100/0.01 = 10k nodes
        - make sure that there's enough humans in a category (e.g. lib or conservative) so bot targeting is possible 
        e.g: if gamma==0.01 & number of bot followers =10, there should be at least 10 nodes in each category
    Note: in measures.tab, user is conservative of user["party"] > 0
"""

import networkx as nx
import json
import pandas as pd
import random
import os
import collections
import numpy as np


def make_network(
    path, files, down_sample=False, target_k_nodes=10000, minimal_target_density=0.01
):
    """
    Make directed network follower -> friend
    Get a subgraph of partisan users
    """

    stats = pd.read_csv(os.path.join(path, files["user_info"]), sep="\t")
    stats = stats.astype({"ID": str}).dropna(axis=0).drop_duplicates()

    with open(os.path.join(path, files["adjlist"])) as fp:
        adjlist = json.load(fp)
    # Convert all node names from int to str. Keys are already str
    adjlist = {k: [str(n) for n in vlist] for k, vlist in adjlist.items()}

    # Get node info if available
    friends = stats[stats["ID"].isin(adjlist.keys())]
    nodes = friends["ID"].values
    print("Nodes that have partisanship info: ", len(nodes))
    user_dict = friends.to_dict(orient="records")
    user_dict = {
        user["ID"]: {
            "Partisanship": user["Partisanship"],
            "Misinformation": user["Misinformation"],
        }
        for user in user_dict
    }
    # make sure the network has comparable number of nodes in each party
    if down_sample:
        party = [info["Partisanship"] for user, info in user_dict.items()]
        binary_party = ["dem" if i > 0 else "rep" for i in party]
        print(
            "Number of nodes in each party: ", dict(collections.Counter(binary_party))
        )
        counts = dict(collections.Counter(binary_party))
        k_nodes = min([i for i in counts.values()])
        rep = [user for user, info in user_dict.items() if info["Partisanship"] > 0]
        dem = [user for user, info in user_dict.items() if info["Partisanship"] < 0]
        print(f"Downsample nodes from one party, sampling {k_nodes} nodes each..")
        sample_nodes = random.sample(rep, k_nodes) + random.sample(dem, k_nodes)
        print(f"Building friend network from sampled {len(sample_nodes)} nodes...")
        nodes = sample_nodes

    G = nx.DiGraph()
    # Directed network follower -> friend
    for s in nodes:
        G.add_node(
            s,
            partisanship=user_dict[s]["Partisanship"],
            misinfo=user_dict[s]["Misinformation"],
        )
        for f in adjlist[s]:
            G.add_edge(s, f)

    average_friends = G.number_of_edges() / G.number_of_nodes()
    # Basic stats
    print(
        f"{G.number_of_nodes()} nodes and {G.number_of_edges()} edges initially"
        f"(average number of friends: {average_friends})"
    )

    return filter_graph(
        G,
        nodes,
        target_k_nodes=target_k_nodes,
        minimal_target_density=minimal_target_density,
    )


def filter_graph(G, nodes_to_filter, target_k_nodes=10000, minimal_target_density=0.01):
    """
    - Reduce the size of network by retaining a k-core=94
    - Reduce density by delete a random sample of edges
    minimal_target_density: default 0.01=default gamma
    """

    ## If target sample graph is much smaller than the actual graph, just delete a random sample nodes first to save time
    if target_k_nodes < 0.5 * len(nodes_to_filter):
        target_to_net_ratio = target_k_nodes / len(nodes_to_filter)
        nodes_to_filter = random.sample(
            nodes_to_filter, int(len(nodes_to_filter) * target_to_net_ratio * 2)
        )
        # nodes_to_filter = list(set(nodes_to_filter) - set(nodes_to_delete))
        print(
            f"Target sample graph is much smaller than the actual graph ({np.round(target_to_net_ratio, 2)}), retaining only a random sample of {len(nodes_to_filter)} nodes..."
        )

    friends = nx.subgraph(G, nodes_to_filter)
    print(
        f"{friends.number_of_nodes()} nodes and {friends.number_of_edges()} edges after filtering"
    )

    # k-core decomposition until ~ 10k nodes in core
    core_number = nx.core_number(friends)
    nodes = friends.number_of_nodes()
    k = 0
    while nodes > target_k_nodes:
        k_core = nx.k_core(friends, k, core_number)
        nodes = k_core.number_of_nodes()
        k += 10
    while nodes < target_k_nodes:
        k_core = nx.k_core(friends, k, core_number)
        nodes = k_core.number_of_nodes()
        k -= 1
    print(
        f"{k}-core has {k_core.number_of_nodes()} nodes, {k_core.number_of_edges()} edges"
    )

    # the network is super dense, so let us delete a random sample of edges
    # MAKE SURE DEGREE OF HUMANS ARE COMPARABLE TO BOTS set target average degree so network is not too dense
    # If not desire, set target_avg_deg= average_friends
    bot_avg_deg = len(nodes_to_filter) * minimal_target_density
    target_avg_deg = bot_avg_deg * 1.5

    friends_core = k_core.copy()
    edges_to_keep = int(friends_core.number_of_nodes() * target_avg_deg)
    edges_to_delete = friends_core.number_of_edges() - edges_to_keep
    deleted_edges = random.sample(friends_core.edges(), edges_to_delete)
    friends_core.remove_edges_from(deleted_edges)
    print(
        f"{k}-core after edge-sampling has {friends_core.number_of_nodes()} nodes, {friends_core.number_of_edges()} edges,"
        f" and average number of friends {friends_core.number_of_edges() / friends_core.number_of_nodes()}"
    )
    return friends_core


if __name__ == "__main__":
    DATA_PATH = "experiments/10242023_v3.3_exps/data"

    RAW_PATH = "data/raw"
    files = {
        # File has 3 columns: ID \t partisanship \t misinformation \n
        "user_info": "measures.tab",
        "adjlist": "anonymized-friends.json",
    }
    friends_core = make_network(
        RAW_PATH,
        files,
        down_sample=True,
        target_k_nodes=1000,
        minimal_target_density=0.01,
    )
    nx.write_gml(friends_core, os.path.join(DATA_PATH, "follower_network.gml"))
