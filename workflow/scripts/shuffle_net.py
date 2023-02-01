""" Script to shuffle the network """

from infosys.graphutils import (
    rewire_preserve_community,
    rewire_preserve_degree,
    rewire_random,
)
import igraph as ig
import sys
import argparse


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
        help="path to input .gml info system network (with bots and humans)",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        action="store",
        dest="outfile",
        type=str,
        required=True,
        help="path to output .gml shuffled network",
    )
    parser.add_argument(
        "--mode",
        action="store",
        dest="mode",
        type=str,
        required=True,
        help="shuffle strategy {community, hub, all}: shuffle network preserving community, hub or shuffle randomly",
    )
    parser.add_argument(
        "--iter",
        action="store",
        dest="iter",
        type=int,
        required=False,
        help="number of times all edges are repeatedly shuffled",
    )

    args = parser.parse_args(args)
    infile = args.infile
    outfile = args.outfile
    mode = args.mode
    try:
        print("Reading network .. ")
        graph = ig.Graph.Read_GML(infile)

        if mode == "community":
            shuffled = rewire_preserve_community(graph, iterations=int(args.iter))
        elif mode == "hub":
            shuffled = rewire_preserve_degree(graph, iterations=int(args.iter))
        else:
            shuffled = rewire_random(graph, probability=1)

        shuffled.write_gml(outfile)

    # Write empty file if exception so smk don't complain
    except Exception as e:
        print(
            "Exception when creating shuffled network. Likely due to assertion error in shuffling"
        )
        print(e)
        shuffled = ig.Graph()
        shuffled.write_gml(outfile)


def shuffle_net(infile, mode, outfile):
    graph = ig.Graph.Read_GML(infile)
    if mode == "community":
        shuffled = rewire_preserve_community(graph)
    elif mode == "hub":
        shuffled = rewire_preserve_degree(graph)
    else:
        shuffled = rewire_random(graph, probability=1)

    shuffled.write_gml(outfile)


if __name__ == "__main__":
    main(sys.argv[1:])
# # DEBUG LOCAL
# infile = 'data/follower_network.gml'
# mode='hub'
# outfile ='data/network_hub.gml'
# shuffle_net(infile, mode, outfile)

