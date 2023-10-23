""" 
Code to (re)produce results in the paper 
"Manipulating the Online Marketplace of Ideas" (Truong et al.)
https://arxiv.org/abs/1907.06130

Main class to run the simulation. Represents an Information System
Inputs: 
    - graph_gml (str): path to igraph .graphml file
    - tracktimestep (bool): if True, track overall quality and exposure to illegal content at each timestep 
    - save_message_info (bool): if True, save all message and newsfeeds info (popularity, mapping of feed-messages, etc. this info is still tracked if flag is False)
    - output_cascades (bool): if True, track & save reshares information to .csv files (for network viz)
    - verbose (bool): if True, print messages 
    - epsilon (float): threshold of quality difference between 2 consecutive timesteps to decide convergence. Default: 0.0001
    - rho (float): weight of the previous timestep's quality in calculating new quality. Default: 0.8
    - mu (float): probability that an agent create new messages. Default: 0.5
    - phi (float): phi in range [0,1] is the probability that a bot message's engagement (engagment) equals 1. Default: 0
    - alpha (int): agent's newsfeed size. Default: 15
    - theta (int): number of copies bots make when creating messages. Default: 1
Important note: 
    - graph_gml: link direction is following (follower -> friend), opposite of info spread!
    - Epsilon value was tested and fixed to the default values above.
        to ensure convergence on the empirical network or network with >=10000 nodes:
            - epsilon <= 0.0001
            - rho >= 0.5
Outputs:
    - measurements (dict): results and information tracked during the simulation. The fields are:
        - quality (float): average quality of all messages from a human newsfeed.
        - diversity (float): entropy calculated from all message's quality
        - discriminative_pow (list): results of the Kendall's correlation coefficient test: [tau, p-value]
        - quality_timestep (list of dict): quality of the system over time 
        - all_messages (list of dict): each dictionary contains the message's information. Dict keys are:
            - id (int): unique identifier for this message
            - agent_id (str): uid of agent originating this message
            - is_by_bot (int): 0 if message is by human, 1 if by bot
            - phi (float): same as phi specified in InfoSys
            - quality (float): quality
            - engagement (float): engagement 
            - human_shares (int): number of shares by humans
            - bot_shares (int): number of shares by bots
            - spread_via_agents (list): uids of agents who reshared this message
            - seen_by_agents (list): uids of agents who are exposed to this message (disregard bot spam)
            - qual_th (int): quality ranking
            - share_th (int): popularity ranking
        - all_feeds (dict): dictionary mapping agent's feed to the messages it contains at convergence
            Structure: {agent_id (str): message ids(list)} 
            - agent_id (str): uid -- unique identifier of an agent (different from vertex id)
        - reshares (list of dict): each dict is a reshare edge. The keys are:
            - message_id (int): unique identifier of a message
            - timestep (int): timestamp of the reshare
            - agent1 (str): uid of the agent spreading the message
            - agent2 (str): uid of the agent resharing the message
"""

from simsom import Message
import simsom.utils as utils
import igraph as ig
import csv
import random
import numpy as np
from collections import Counter, defaultdict
import concurrent.futures
import queue
from copy import deepcopy
import sys


class SimSom:
    def __init__(
        self,
        graph_gml,
        tracktimestep=True,
        save_message_info=True,
        output_cascades=False,
        verbose=False,
        n_threads=7,
        epsilon=0.0001,  # Don't change this value
        rho=0.8,  # Don't change this value, check note above
        mu=0.5,
        phi=0,
        alpha=15,
        theta=1,
    ):
        print("SimSomV3.3 all agents activated (bug fixed)")
        # graph object
        self.graph_gml = graph_gml

        # params
        self.epsilon = epsilon
        self.rho = rho
        self.mu = mu
        self.phi = phi
        self.alpha = alpha
        self.theta = theta

        # simulation options
        self.n_threads = n_threads
        self.verbose = verbose
        self.tracktimestep = tracktimestep
        self.save_message_info = save_message_info
        self.output_cascades = output_cascades

        # bookkeeping
        #### debugging
        # number of unique messages ever created (including extincted ones)
        self.num_message_unique = 0
        self.num_human_messages = 0  # number of messages across all human feeds
        # number of unique messages across all human feeds
        self.num_human_messages_unique = 0
        #### debugging

        self.quality_timestep = []  # list of overall quality at each timestep

        self.message_dict = []  # list of all message objects
        self.all_messages = {}  # dict of message_id - message objects
        self.message_metadata = {}
        self.agent_feeds = {}  # dict of agent_uid - [message_ids]

        self.exposure_timestep = []  # list of exposure to bot messages at each timestep

        # convergence check
        self.quality_diff = 1
        self.quality = 1
        self.time_step = 0
        # track min, mean, max message age over time
        self.age_timestep = []
        # stats
        self.exposure = 0
        try:
            self.network = ig.Graph.Read_GML(self.graph_gml)
            if verbose is True:
                print(self.network.summary(), flush=True)

            self.n_agents = self.network.vcount()
            self.human_uids = [n["uid"] for n in self.network.vs if n["bot"] == 0]
            self.is_human_only = (
                True if len(self.human_uids) == self.n_agents else False
            )
            # init an empty feed for all agents
            # self.agent_feeds = {agent["uid"]: ([], []) for agent in self.network.vs}
            self.agent_feeds = defaultdict(lambda: ([], [], []))
            if verbose is True:
                # sanity check: calculate number of followers
                in_deg = [self.network.degree(n, mode="in") for n in self.network.vs]
                print(
                    "Graph Avg in deg", round(sum(in_deg) / len(in_deg), 2), flush=True
                )

        except Exception as e:
            raise Exception(
                f"Unable to read graph file. File doesn't exist of corrupted: {graph_gml}",
                e,
            )

    def simulation(self, reshare_fpath=""):
        """
        Driver for simulation.
        This function calls simulation_step() N times at each timestep (where N is number of agents).
        It then updates the overall quality at each timestep and checks for convergence
        Inputs (optional):
            - reshare_fpath: path to .csv file containing reshare cascade info
        """

        if self.output_cascades is True:
            self.reshare_fpath = reshare_fpath
            reshare_fields = ["message_id", "timestep", "source", "target"]
            with open(self.reshare_fpath, "w", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(reshare_fields)

        while self.quality_diff > self.epsilon:
            num_messages = sum([len(feed) for feed, _, _ in self.agent_feeds.values()])
            if self.verbose:
                print(
                    f"- time_step = {self.time_step}, q = {np.round(self.quality, 6)}, diff = {np.round(self.quality_diff, 6)}, existing human/all messages: {self.num_human_messages}/{num_messages}, unique human messages: {self.num_human_messages_unique}, total created: {self.num_message_unique}",
                    flush=True,
                )
                print("  exposure to harmful content: ", self.exposure, flush=True)

            self.time_step += 1
            if self.tracktimestep is True:
                self.quality_timestep += [self.quality]
                self.exposure_timestep += [self.measure_exposure()]

            # Propagate messages
            self.simulation_step()

            self.update_quality()

        # return feeds, self.message_metadata, self.quality
        # Call this before calculating tau and diversity!!
        try:
            self.message_dict = self._return_all_message_info()

            measurements = {
                "quality": self.quality,
                "diversity": self.measure_diversity(),
                "discriminative_pow": self.measure_kendall_tau(),
            }

            if self.save_message_info is True:
                # Save agents' newsfeed info & message popularity
                measurements["quality_timestep"] = self.quality_timestep
                measurements["exposure_timestep"] = self.exposure_timestep
                measurements["age_timestep"] = self.age_timestep
                measurements["all_messages"] = self.message_dict
                # convert np arrays to list to JSON serialize
                # Note: a.tolist() is almost the same as list(a), except that tolist changes numpy scalars to Python scalars
                for agent_id, feed_tuple in self.agent_feeds.items():
                    measurements["feeds_message_ids"] = {
                        agent_id: feed_tuple[0].tolist()
                    }
                    measurements["feeds_shares"] = {agent_id: feed_tuple[1].tolist()}
                    measurements["feeds_ages"] = {agent_id: feed_tuple[2].tolist()}
        except Exception as e:
            raise Exception(
                'Failed to output a measurement, e.g,["quality", "diversity", "discriminative_pow"] or save message info.',
                e,
            )

        return measurements

    def simulation_step(self):
        """
        During each simulation step, agents reshare or post new messages (in parallel).
        After `n` agents have done their actions and return requests to modify their follower feeds, messages are not yet propagated in the network.
        This step aggregates popularity of the messages (if multiple agents reshare the same message) and distributes messages to newsfeeds.
        """

        all_agents = self.network.vs  # list of all agent ids
        q = queue.Queue()

        def post_message(agent):
            modify_requests = self.user_step(agent)
            if len(modify_requests) > 0:
                q.put(modify_requests)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.n_threads
        ) as executor:
            if self.time_step == 1:
                print(
                    f" - Simulation running on {executor._max_workers} threads",
                    flush=True,
                )
            for _ in executor.map(post_message, all_agents):
                try:
                    pass
                except Exception as e:
                    print(e, flush=True)
                    sys.exit("Propagation (post_message) failed.")

        update_list = defaultdict(list)

        ### Aggregate message popularity
        # each item in queue is a list of requests from an agent to modify its follower feeds
        # e.g.: item= [(follower1, [mess1]), (follower2, [mess1]), .. ]
        # or item= [(follower1, [mess1]*theta), (follower2, [mess1]*theta), .. ] if the agent is a bot
        # iterates over all agent update requests, if exists overlap update popularity
        for item in q.queue:
            for agent_id, message_ids in item:
                update_list[agent_id] += message_ids
        # eg:
        # {'a1': defaultdict(int, {'1': 4, '2': 1, '3': 1, '6': 1, '7': 1}),
        # 'a2': defaultdict(int, {'2': 1, '1': 1, '4': 1})}
        # print("Update list:", update_list, flush=True)

        ### Distribute posts to newsfeeds
        # update_list: {agent_id: {message_id: popularity}}

        ages = []
        for agent_id, message_list in update_list.items():
            message_counts = Counter(message_list)
            message_ids = list(message_counts.keys())
            no_shares = list(message_counts.values())
            try:
                avg_age = self._bulk_add_messages_to_feed(
                    agent_id, np.array(message_ids), np.array(no_shares)
                )

                ages += [avg_age]
            except Exception as e:
                print(e, flush=True)
                sys.exit("Propagation (bulk_add_messages_to_feed) failed.")
        # print("Agent feeds after updating:", self.agent_feeds, flush=True)

        self.age_timestep += [
            (min(ages), sum(ages) / len(ages) if len(ages) > 0 else 0, max(ages))
        ]
        return

    def user_step(self, agent):
        """
        Represents an action by `agent` at each timestep. `agent` can reshare from their own feeds or post new messages.
        Returns `agent` suggested changes: a tentative list of newsfeeds that `agent` wants to post message on
        After returned from spawning, the simulator will consolidate this list of feeds with other agents' suggested changes.
        Keep track of reshare information if output_cascades is True.
        Input:
            agent (igraph.Vertex): node representing an agent
        Output:
            modify_requests (list of tuples): list of requests from `agent` to modify their follower feeds.
            A tuple represents (follower, [list of message_ids])
        """
        try:
            agent_id = agent["uid"]
            feed, no_shares, ages = self.agent_feeds[agent_id]

            # update agent exposure to messages in its feed at login
            self._update_exposure(feed, agent)

            # posting
            message_id = self._create_post(agent)
            # book keeping (for all messages)
            self._update_message_popularity(message_id, agent)

            # spread: make requests to add message to top of follower's feed (theta copies if poster is bot to simulate flooding)
            follower_idxs = self.network.predecessors(agent)  # return list of int
            follower_uids = [
                n["uid"] for n in self.network.vs if n.index in follower_idxs
            ]

            modify_requests = []

            for follower in follower_uids:
                if self.output_cascades is True:
                    self._update_reshares(message_id, agent_id, follower)

                if agent["bot"] == True:
                    modify_requests.append((follower, [message_id] * self.theta))
                else:
                    modify_requests.append((follower, [message_id]))
        except Exception as e:
            raise Exception("Error in user_step: ", e)

        return modify_requests

    def _create_post(self, agent):
        """
        Create a new message or reshare a message from newsfeed
        Returns a message id (int)
        """
        # TODO: Do we want to keep the popularity of messages at each timestep?
        # Or keep a copy of agent's feed (message-popularity) for each timestep?

        try:
            newsfeed = self.agent_feeds[agent["uid"]]

            messages, _, _ = newsfeed

            # return messages created by the agent via resharing or posting
            if len(newsfeed[0]) > 0 and random.random() > self.mu:
                # retweet a message from feed selected based on its ranking (engagement, popularity and recency)
                # Note: random.choices() weights input doesn't have to be normalized
                r_messages, ranking = self._rank_newsfeed(newsfeed)

                # make sure ranking order is correct
                # assert (r_messages == messages).all()
                (message_id,) = random.choices(messages, weights=ranking, k=1)
            else:
                # new message
                self.num_message_unique += 1
                message = Message(
                    id=self.num_message_unique,
                    is_by_bot=agent["bot"],
                    phi=self.phi,
                )

                self.all_messages[message.id] = message
                message_id = message.id
        except Exception as e:
            print(e)
            raise ValueError("Failed to create a new message.")
        return message_id

    def update_quality(self):
        """
        Update quality using exponential moving average to ensure stable state at convergence
        Forget the past slowly, i.e., new_quality = 0.8 * avg_quality(at t-1) + 0.2 * current_quality
        """

        new_quality = (
            self.rho * self.quality + (1 - self.rho) * self.measure_average_quality()
        )
        self.quality_diff = (
            abs(new_quality - self.quality) / self.quality if self.quality > 0 else 0
        )
        self.quality = new_quality

    def measure_kendall_tau(self):
        """
        Calculates the discriminative power of the system
        (Invoke only after self._return_all_message_info() is called)
        """

        quality_ranked = sorted(self.message_dict, key=lambda m: m["quality"])
        for ith, elem in enumerate(quality_ranked):
            elem.update({"qual_th": ith})

        share_ranked = sorted(quality_ranked, key=lambda m: m["human_shares"])
        for ith, elem in enumerate(share_ranked):
            elem.update({"share_th": ith})

        idx_ranked = sorted(share_ranked, key=lambda m: m["id"])
        ranking1 = [message["qual_th"] for message in idx_ranked]
        ranking2 = [message["share_th"] for message in idx_ranked]
        tau, p_value = utils.kendall_tau(ranking1, ranking2)
        return tau, p_value

    def measure_average_quality(self):
        """
        Calculates the average quality across human messages in system
        """

        total = 0
        count = 0

        # keep track of no. messages for verbose debug
        human_message_ids = []
        for u in self.human_uids:
            message_ids, _, _ = self.agent_feeds[u]
            message_ids = list(message_ids)
            for message_id in message_ids:
                total += self.all_messages[message_id].quality
                count += 1
            human_message_ids += message_ids

        self.num_human_messages = count
        self.num_human_messages_unique = len(set(human_message_ids))

        return total / count if count > 0 else 0

    def measure_diversity(self):
        """
        Calculates the diversity of the system using entropy (in terms of unique messages)
        (Invoke only after self._return_all_message_info() is called)
        """

        humanshares = []
        for human, feed in self.agent_feeds.items():
            message_ids, _, _ = feed
            for message_id in message_ids:
                humanshares += [message_id]
        message_counts = Counter(humanshares)
        # return a list of [(messageid, count)], sorted by id
        count_byid = sorted(dict(message_counts).items())
        humanshares = np.array([m[1] for m in count_byid])

        hshare_pct = np.divide(humanshares, sum(humanshares))
        diversity = utils.entropy(hshare_pct) * -1
        # Note that (np.sum(humanshares)+np.sum(botshares)) !=self.num_messages because a message can be shared multiple times
        return diversity

    def measure_exposure(self):
        """
        Calculate number of exposures to low-quality/illegal messages
        """
        # TODO: Measure exposure before or after removal? (If after, we have to ignore those that have been removed)
        illegal_messages = [
            mid for mid, m in self.all_messages.items() if m.quality == 0
        ]
        exposure = 0
        for message_id in illegal_messages:
            exposure += len(self.message_metadata[message_id]["seen_by_agents"])

        self.exposure = exposure
        return exposure

    def _bulk_add_messages_to_feed(self, target_id, incoming_ids, incoming_shares):
        """
        Add message to agent's feed in bulk, forget the oldest if feed size exceeds self.alpha (first in first out)
        If a message to be added is already in the feed, update its popularity and move to beginning of feed (youngest)
        Inputs:
        - target_id (str): uid of agent resharing the message -- whose feed we're adding the message to
        - incoming_ids (np.array of ints): ids of messages to be added
        - incoming_shares (np.array  of int): number of shares of each message. incoming_shares[i] is no. shares of message i
        Note: feed[0] is the most recent item in the newsfeed
        """
        try:
            newsfeed = self.agent_feeds[target_id]
            messages, no_shares, ages = newsfeed
            avg_age = np.mean(ages) if len(ages) > 0 else 0
            if len(newsfeed[0]) == 0:
                updated_feed = (
                    incoming_ids,
                    incoming_shares,
                    np.zeros(len(incoming_ids), dtype=int),
                )
            elif len(set(messages) & set(incoming_ids)) > 0:
                if self.verbose:
                    print(f"  ids   : {incoming_ids} -> {messages}")
                    print(f"  shares: {incoming_shares} -> {no_shares}")
                updated_feed = self._update_feed_handle_overlap(
                    newsfeed, incoming_ids, incoming_shares
                )
            else:
                messages = np.insert(messages, 0, incoming_ids, axis=0)
                no_shares = np.insert(no_shares, 0, incoming_shares, axis=0)
                ages = np.ones(len(ages), dtype=int)
                ages = np.insert(
                    ages, 0, np.zeros(len(incoming_ids), dtype=int), axis=0
                )

                updated_feed = (messages, no_shares, ages)

            # clip the agent's feed if exceeds alpha
            if len(updated_feed[0]) > self.alpha:
                updated_feed = self._handle_oversized_feed(updated_feed)

            # rank messages

            # for i in updated_feed:
            #     assert isinstance(i, np.ndarray)

            self.agent_feeds[target_id] = updated_feed

        except Exception as e:
            raise Exception(f"Fail to add messages to {target_id}'s feed", e)

        return avg_age

    def _rank_newsfeed(self, newsfeed, w_e=1 / 3, w_p=1 / 3, aging_lambda=0.9):
        """
        Calculate probability of being reshared for messages in the newsfeed using the formula:
        $$ P(m) = w_ee_m + w_p\frac{p_m}{\sum^{\alpha}_{j\in M_i}p_j} + w_rr_m $$
        where $e_m, p_m, r_m$ are the engagement, no_shares and recency of a message and $w_e, w_p, w_r$ are their respective weights.

        $r= \lambda^{age}$: is the recency of the message.

        Default values:
        - $w_e = w_p = w_r = 1/3$
        - $\lambda = 0.9$

        Input:
            newsfeed (tuple of np.arrays): (message_ids, no_shares, ages), represents an agent's news feed
        """
        messages, shares, ages = newsfeed

        popularity = shares / np.sum(shares)  # relative no_shares

        lambdas = np.empty(len(ages), dtype=float)
        lambdas.fill(aging_lambda)
        recency = lambdas**ages

        engagement = np.array(
            [self.all_messages[message].engagement for message in messages]
        )
        w_r = 1 - (w_e + w_p)
        ranking = np.sum([w_e * engagement, w_p * popularity, w_r * recency], axis=0)

        # # normalize
        # ranking = utils.normalize(ranking)

        return messages, ranking

    def _update_feed_handle_overlap(self, target_feed, incoming_ids, incoming_shares):
        """
        Update feed with new messages.
        Handle overlapping: if message already exists, reset age to 0. Increment age for the rest of the messages
        New messages are appended to the beginning of the feed, existing messages order is maintained
        - target_feed (tuple of lists): (message_ids, no_shares, ages), represents an agent's news feed
        """
        try:
            messages, no_shares, ages = target_feed

            # return sorted intersection
            overlap, x_ind, y_ind = np.intersect1d(
                messages, incoming_ids, return_indices=True
            )
            # print(new_messages, new_shares, new_ages)
            if self.verbose:
                # print(f"incoming ids : {incoming_ids} --> feed: {messages}")
                # print(f"no_shares : {incoming_shares} --> feed: {no_shares}")
                print(
                    f"  incoming age : {np.zeros(len(incoming_ids))} --> feed: {ages}"
                )

                print(
                    f"   overlap message between {messages} and {incoming_ids} are: {overlap}"
                )
                print("   update no_share and age of overlapping messages.. ")
                print(
                    f"   before:  messages: {messages}, shares: {no_shares}, ages: {ages}"
                )

            # index the overlap message from 2 arrays
            mask_x, mask_y = np.zeros(len(messages), bool), np.zeros(
                len(incoming_ids), bool
            )
            mask_x[[x_ind]], mask_y[[y_ind]] = True, True

            # update no_shares and age of existing messages
            no_shares[mask_x] += incoming_shares[mask_y]

            # add age to all other messages
            ages += np.ones(len(ages), dtype=int)
            # reset age existing messages
            ages[mask_x] = np.zeros(len(y_ind))

            if self.verbose:
                print(
                    f"   after:  messages: {messages}, shares: {no_shares}, ages: {ages}"
                )
            # push new messages into the feed (only the non-overlapping messages)
            no_shares = np.insert(no_shares, 0, incoming_shares[~mask_y])
            messages = np.insert(messages, 0, incoming_ids[~mask_y])
            ages = np.insert(ages, 0, np.zeros(len(incoming_shares[~mask_y])))
            if (ages != np.zeros(len(ages))).all():
                print("")
            if self.verbose:
                print(
                    f"   updated: messages: {messages}, shares: {no_shares}, ages: {ages}"
                )
            updated_feed = messages, no_shares, ages
        except Exception as e:
            raise Exception("Error in handle_overlap: ", e)

        return updated_feed

    def _handle_oversized_feed(self, newsfeed):
        """
        Handles oversized newsfeed
        Returns the newsfeed (tuple of lists) where the oldest message is removed
        Input:
            feed (tuple - (list of int, list of int)): (list of mess_ids - list of popularities), represents an agent's news feed
        """
        # Remove messages based on age - oldest first
        messages, shares, ages = newsfeed

        sorted_by_age = sorted(zip(messages, shares, ages), key=lambda x: x[2])
        sorted_messages, sorted_shares, sorted_ages = [
            np.array(i) for i in zip(*sorted_by_age)
        ]

        updated_feed = (
            sorted_messages[: self.alpha],
            sorted_shares[: self.alpha],
            sorted_ages[: self.alpha],
        )

        assert len(updated_feed[0]) <= self.alpha
        # for i in updated_feed:
        #     assert isinstance(i, np.ndarray)
        return updated_feed

    def _return_all_message_info(self):
        """
        Combine message attributes (quality, engagement) with popularity data (spread_via_agents, seen_by_agents, etc.)
        Return a list of dict, where each dict contains message metadata
        """
        # for message in self.all_messages.values():
        #     assert isinstance(message, Message)
        # Be careful: convert to dict to avoid infinite recursion
        messages = [message.__dict__ for message in self.all_messages.values()]
        for message_dict in messages:
            message_dict.update(self.message_metadata[message_dict["id"]])
        return messages

    def _update_reshares(self, message, source, target):
        """
        Update the reshare cascade information to a file is `self.output_cascades`==True
        Input:
        - message (int): id of message being reshared
        - source (str): uid of agent spreading the message
        - target (str): uid of agent resharing the message
        """

        with open(self.reshare_fpath, "a", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow([message, self.time_step, source, target])

        return

    def _update_exposure(self, feed, agent):
        """
        Update human's exposure to message whenever an agent is activated (equivalent to logging in)
        (when flag self.output_cascades is True)
        Input:
        - feed (list of ints): ids of messages in agent's news feed
        - agent (Graph vertex): agent resharing the message
        """

        for message_id in feed:
            self.message_metadata[message_id]["seen_by_agents"] += [agent["uid"]]

        # TODO: Track popularity at each timestep. Is this the same as infeed of agents?
        # Previously:
        # seen = []
        # for message in feed:
        #     if message.id not in seen:
        #         self.message_metadata[message.id]["seen_by_agents"] += [agent["uid"]]
        #     self.message_metadata[message.id]["infeed_of_agents"] += [agent["uid"]]
        #     seen += [message.id]

        return

    def _update_message_popularity(self, message_id, agent):
        """
        Update information of a message whenever it is reshared.
        Input:
        - message_id (str): id of message being reshared
        - agent (Graph vertex): agent resharing the message
        """

        if message_id not in self.message_metadata.keys():
            # "agent_id": agent who first reshared this message (also creator)
            self.message_metadata[message_id] = {
                "agent_id": agent["uid"],
                # "is_by_bot": message.is_by_bot,
                "human_shares": 0,
                "bot_shares": 0,
                "spread_via_agents": [],
                "seen_by_agents": [],
            }

        self.message_metadata[message_id]["spread_via_agents"] += [agent["uid"]]

        if agent["bot"] == 0:
            self.message_metadata[message_id]["human_shares"] += 1
        else:
            self.message_metadata[message_id]["bot_shares"] += self.theta
        return

    def __repr__(self):
        """
        Define the representation of the object.
        """
        bot_params = "\n".join(
            [
                f" Network of humans and bots",
                f"Bot paramters:",
                f" - phi (deception): {self.phi}",
                f" - theta (flooding):{self.theta}",
            ]
        )

        return "\n".join(
            [
                f"<{self.__class__.__name__}() object> constructed from {self.graph_gml}",
                f"Simulation controls:",
                f" - epsilon: {self.epsilon}",
                f" - rho:     {self.rho}",
                f"Propagation parameters:",
                f" - mu (posting rate): {self.mu}",
                f" - alpha (feedsize):  {self.alpha}",
                f"Network contains one type of agents (no bots): {self.is_human_only}",
                f"{bot_params}",
            ]
        )
