""" Script to initialize Information network based on a .json configuration file """

import simsom.graphutils as graphutils
import simsom.utils as utils
import networkx as nx
import sys
import argparse
import json
import igraph


def init_igraph(net_specs):
    legal_specs = utils.remove_illegal_kwargs(net_specs, graphutils.init_net)
    # print(legal_specs)
    G = graphutils.init_net(**legal_specs)
    return G


def init_nx_graph(net_specs):
    legal_specs = utils.remove_illegal_kwargs(net_specs, graphutils.init_net)
    # print(legal_specs)
    G = graphutils.init_net(**legal_specs)
    return G


def main(args):
    parser = argparse.ArgumentParser(
        description="initialize info system graph from human empirical network",
    )

    parser.add_argument(
        "-i",
        "--infile",
        action="store",
        dest="infile",
        type=str,
        required=True,
        help="path to input .gml follower network file",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        action="store",
        dest="outfile",
        type=str,
        required=True,
        help="path to out .gml info system network file (with bots and humans)",
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        dest="config",
        type=str,
        required=True,
        help="path to all configs file",
    )
    parser.add_argument(
        "-m",
        "--mode",
        action="store",
        dest="mode",
        type=str,
        required=True,
        help="mode of implementation",
    )

    args = parser.parse_args(args)
    infile = (
        args.infile
    )  # infile is a json containing list of {"beta": 0.0, "gamma": 0.0}
    outfile = args.outfile
    configfile = args.config
    mode = args.mode

    net_spec = json.load(open(configfile, "r"))
    if net_spec["human_network"] is not None:
        net_spec.update({"human_network": infile})

    # print(net_spec)
    try:
        if mode == "igraph":
            G = init_igraph(net_spec)
            G.write_gml(outfile)
        else:
            G = init_nx_graph(net_spec)
            nx.write_gml(G, outfile)

    # Write empty file if exception so smk don't complain
    except Exception as e:
        print(
            "Exception when making infosystem network. \n Likely due to sampling followers in targeting criteria."
        )
        print(e)

        G = igraph.Graph()
        G.write_gml(outfile)


if __name__ == "__main__":
    main(sys.argv[1:])

