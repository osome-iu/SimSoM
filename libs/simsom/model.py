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
    - sigma (int): agent's newsfeed size. Default: 15
    - mu (float): probability that an agent create new messages. Default: 0.5
    - phi (float): phi in range [0,1] is the probability that a bot message's appeal equals 1. Default: 0
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
            - appeal (float): appeal 
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

from simsom.message import Message
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
import warnings
import os


class SimSom:
    def __init__(
        self,
        graph_gml,
        tracktimestep=True,
        save_message_info=True,
        save_newsfeed_message_info=False,
        output_cascades=False,
        verbose=False,
        logger=None,
        debug=False,
        n_threads=7,
        epsilon=0.0001,  # Don't change this value
        rho=0.8,  # Don't change this value, check note above
        sigma=15,
        mu=0.5,
        phi=0,
        theta=1,
        appeal_exp=5,
        converge_by="quality",  # ['steps', 'quality']
        max_steps=100,
    ):
        # graph object
        self.graph_gml = graph_gml

        # params
        self.epsilon = epsilon
        self.rho = rho
        self.sigma = sigma
        self.mu = mu
        self.phi = phi
        self.theta = theta
        self.appeal_exp = appeal_exp

        # simulation options
        self.n_threads = n_threads
        self.verbose = verbose
        self.logger = logger
        self.debug = debug
        self.tracktimestep = tracktimestep
        self.save_message_info = save_message_info
        # Track message information relative to each feed at each timestep
        ## !! Memory intensive !!!
        self.save_newsfeed_message_info = save_newsfeed_message_info
        self.output_cascades = output_cascades

        #### debugging
        # number of unique messages ever created (including extincted ones)
        self.num_message_unique = 0
        self.num_human_messages = 0  # number of messages across all human feeds
        # number of unique messages across all human feeds
        self.num_human_messages_unique = 0
        #### debugging

        # bookkeeping
        self.quality_timestep = []  # list of overall quality at each timestep
        self.message_dict = []  # list of all message objects
        self.all_messages = {}  # dict of message_id - message objects
        self.message_metadata = {}
        self.agent_feeds = {}  # dict of agent_uid - [message_ids]

        # each item is a 2d numpy array of message info
        # each column is a message, each row is the information: messages, appeal, popularity, recency, ages, ranking, is_chosen
        self.reshare_tracking = []

        self.exposure_timestep = []  # list of exposure to bot messages at each timestep

        # convergence check
        self.converge_by = converge_by
        self.max_steps = max_steps
        if self.converge_by == "quality":
            self.converge_condition = "self.quality_diff > self.epsilon"
        elif self.converge_by == "steps":
            self.converge_condition = "self.time_step < self.max_steps"
        else:
            self.converge_condition = "(self.time_step < self.max_steps) or (self.quality_diff > self.epsilon)"

        self.quality_diff = 1
        self.quality = 1
        self.time_step = 0
        # stats
        self.exposure = 0
        try:
            self.network = ig.Graph.Read_GML(self.graph_gml)
            if self.logger is None:
                self.logger = utils.get_file_logger(
                    log_dir="logs",
                    full_log_path=os.path.join("logs", f"simulation.log"),
                    also_print=True,
                )
            if verbose:
                self.logger.info(self.network.summary())

            self.n_agents = self.network.vcount()
            self.human_uids = [n["uid"] for n in self.network.vs if n["bot"] == 0]
            self.is_human_only = (
                True if len(self.human_uids) == self.n_agents else False
            )
            # init an empty feed for all agents
            # self.agent_feeds = {agent["uid"]: ([], []) for agent in self.network.vs}
            self.agent_feeds = defaultdict(lambda: ([], [], []))
            if verbose:
                # sanity check: calculate number of followers
                in_deg = [self.network.degree(n, mode="in") for n in self.network.vs]
                self.logger.info(
                    "Graph Avg in deg", round(sum(in_deg) / len(in_deg), 2)
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

        # Run simulation until either or both convergence condition is met
        while eval(self.converge_condition):
            num_messages = sum([len(feed) for feed, _, _ in self.agent_feeds.values()])
            if self.verbose:
                self.logger.info(
                    f"- time_step = {self.time_step}, q = {np.round(self.quality, 6)}, diff = {np.round(self.quality_diff, 6)}, existing human/all messages: {self.num_human_messages}/{num_messages}, unique human messages: {self.num_human_messages_unique}, total created: {self.num_message_unique}"
                )
                self.logger.info("  exposure to harmful content: ", self.exposure)

            self.time_step += 1
            if self.tracktimestep is True:
                self.quality_timestep += [self.quality]
                self.exposure_timestep += [self.measure_exposure()]
                # record the timestep at which simulation would end with (rho; epsilon)
                if self.quality_diff < self.epsilon:
                    self.converged_rhoepsilon_timestep = self.time_step

            # Propagate messages
            self.simulation_step()

            self.update_quality()

        ## Simulation finished - saving data
        try:
            # return feeds, self.message_metadata, self.quality
            # Call this before calculating tau and diversity!!
            self.message_dict = self._return_all_message_info()

            measurements = {
                "quality": self.quality,
                "diversity": self.measure_diversity(),
                "discriminative_pow": self.measure_kendall_tau(),
            }

            if self.tracktimestep:
                # Save system measurements and message metadata
                measurements["quality_timestep"] = self.quality_timestep
                measurements["exposure_timestep"] = self.exposure_timestep

                measurements["converged_rhoepsilon_timestep"] = (
                    self.converged_rhoepsilon_timestep
                )

            if self.save_message_info:

                measurements["all_messages"] = self.message_dict

                ## Save agents' newsfeed info at the end of simulation (used to determine which messages are obsolete)
                # convert np arrays to list to JSON serialize
                # Note: a.tolist() is almost the same as list(a), except that tolist changes numpy scalars to Python scalars
                # Only save data for agents whose feeds are not empty
                measurements["feeds_message_ids"] = {}
                measurements["feeds_shares"] = {}
                measurements["feeds_ages"] = {}
                for agent_id, feed_tuple in self.agent_feeds.items():
                    if len(feed_tuple[0]) > 0:
                        measurements["feeds_message_ids"][agent_id] = feed_tuple[
                            0
                        ].tolist()
                        measurements["feeds_shares"][agent_id] = feed_tuple[1].tolist()
                        measurements["feeds_ages"][agent_id] = feed_tuple[2].tolist()

            if self.save_newsfeed_message_info:
                # Save message info relative to each newsfeed
                # convert message tracking info into a big np array
                all_reshare_tracking = np.hstack(self.reshare_tracking)
                reshared_message_dict = dict()
                # messages, appeal, shares, recency, ages, ranking
                tracking_keys = [
                    "messages",
                    "appeal",
                    "no_shares",
                    "recency",
                    "ages",
                    "ranking",
                    "is_chosen",
                ]
                for idx, key in enumerate(tracking_keys):
                    reshared_message_dict[key] = all_reshare_tracking[idx].tolist()

                measurements["reshared_messages"] = reshared_message_dict
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

        # all_agents = self.network.vs  # list of all agent ids
        order = np.random.permutation(range(self.n_agents))
        all_agents = [self.network.vs[idx] for idx in order]

        q = queue.Queue()

        def post_message(agent):
            modify_requests = self.user_step(agent)
            if len(modify_requests) > 0:
                # debugging: tracking the originator of the modify request
                q.put(modify_requests)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.n_threads
        ) as executor:
            if self.time_step == 1:
                self.logger.info(
                    f" - Simulation running on {executor._max_workers} threads"
                )
            for _ in executor.map(post_message, all_agents):
                try:
                    pass
                except Exception as e:
                    self.logger.error(e)
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
        # print("Update list:", update_list)

        ### Distribute posts to newsfeeds
        # update_list: {agent_id: {message_id: popularity}}

        for agent_id, message_list in update_list.items():
            message_counts = Counter(message_list)
            message_ids = list(message_counts.keys())
            no_shares = list(message_counts.values())
            try:
                agent_message_ages = self.agent_feeds[agent_id][2]
                self._bulk_add_messages_to_feed(
                    agent_id, np.array(message_ids), np.array(no_shares)
                )
            except Exception as e:
                self.logger.error(e)
                sys.exit("Propagation (bulk_add_messages_to_feed) failed.")
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
            # book keeping: record that this agent shared a message
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

            messages, no_shares, ages = newsfeed

            # return messages created by the agent via resharing or posting
            if len(newsfeed[0]) > 0 and random.random() > self.mu:
                # retweet a message from feed selected based on its ranking (appeal, popularity and recency)
                # Note: random.choices() weights input doesn't have to be normalized
                # message info: 2d np array where each column is a message,
                # each row is the information: messages, appeal, popularity, recency, ages, ranking
                message_info, ranking = self._rank_newsfeed(newsfeed)

                # make sure ranking order is correct
                # assert (message_info[0] == messages).all()
                (message_id,) = random.choices(messages, weights=ranking, k=1)
                if self.save_newsfeed_message_info:
                    is_chosen = np.zeros(len(messages))
                    is_chosen[np.where(messages == message_id)] = 1
                    message_info = np.vstack([message_info, is_chosen])
                    self.reshare_tracking.append(message_info)
            else:
                # new message
                self.num_message_unique += 1
                message = Message(
                    id=self.num_message_unique,
                    is_by_bot=agent["bot"],
                    phi=self.phi,
                    appeal_exp=self.appeal_exp,
                )

                self.all_messages[message.id] = message
                message_id = message.id
        except Exception as e:
            self.logger.error(e)
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
        Calculate exposure to bad actor messages
        Using Facebook's definition for prevalence of problematic content: = No. Views for that content / Estimated total content view
        """
        # TODO: Measure exposure before or after removal? (If after, we have to ignore those that have been removed)
        total_exposure = 0
        bad_exposure = 0

        for message_id, message in self.all_messages.items():
            if message.quality == 0:
                bad_exposure += len(self.message_metadata[message_id]["seen_by_agents"])
            total_exposure += len(self.message_metadata[message_id]["seen_by_agents"])

        self.exposure = bad_exposure / total_exposure if total_exposure > 0 else 0
        return self.exposure

    def _bulk_add_messages_to_feed(self, target_id, incoming_ids, incoming_shares):
        """
        Add message to agent's feed in bulk, forget the oldest if feed size exceeds self.sigma (first in first out)
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
            if len(newsfeed[0]) == 0:
                updated_feed = (
                    incoming_ids,
                    incoming_shares,
                    np.zeros(len(incoming_ids), dtype=int),
                )
            elif len(set(messages) & set(incoming_ids)) > 0:
                if self.debug:
                    self.logger.info(f"  ids   : {incoming_ids} -> {messages}")
                    self.logger.debug(f"  shares: {incoming_shares} -> {no_shares}")
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

            # clip the agent's feed if exceeds sigma
            if len(updated_feed[0]) > self.sigma:
                updated_feed = self._handle_oversized_feed(updated_feed)

            # rank messages

            # for i in updated_feed:
            #     assert isinstance(i, np.ndarray)

            self.agent_feeds[target_id] = updated_feed

            return True
        except Exception as e:
            raise Exception(f"Fail to add messages to {target_id}'s feed", e)

    def _rank_newsfeed(self, newsfeed):
        """
        Calculate probability of being reshared for messages in the newsfeed using the formula:
        $$ P(m) = w_ee_m + w_p\frac{p_m}{\sum^{\sigma}_{j\in M_i}p_j} + w_rr_m $$
        where $e_m, p_m, r_m$ are the appeal, no_shares and recency of a message and $w_e, w_p, w_r$ are their respective weights.

        The recency of a message m follow a stretched exponential distribution estimated empirically by Wu & Huberman
        https://www.pnas.org/doi/10.1073/pnas.0704916104
        $r ~ e^{-0.4t^{0.4}}$ where t is the time step


        Input:
            newsfeed (tuple of np.arrays): (message_ids, no_shares, ages), represents an agent's news feed
        """
        messages, shares, ages = newsfeed
        appeal = np.array([self.all_messages[message].appeal for message in messages])
        recency = np.exp(-0.4 * (ages**0.4))

        ranking = appeal * shares * recency / np.sum(appeal * shares * recency)

        # assert len(popularity) == len(appeal) == len(ranking)

        ## tracking
        message_info = np.vstack([messages, appeal, shares, recency, ages, ranking])
        return message_info, ranking

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
            if self.debug:
                # self.logger.debug(f"incoming ids : {incoming_ids} --> feed: {messages}")
                # self.logger.debug(f"no_shares : {incoming_shares} --> feed: {no_shares}")
                self.logger.debug(
                    f"  incoming age : {np.zeros(len(incoming_ids))} --> feed: {ages}"
                )

                self.logger.debug(
                    f"   overlap message between {messages} and {incoming_ids} are: {overlap}"
                )
                self.logger.debug(
                    "   update no_share and age of overlapping messages.. "
                )
                self.logger.debug(
                    f"   before:  messages: {messages}, shares: {no_shares}, ages: {ages}"
                )

            # index the overlap message from 2 arrays
            mask_x, mask_y = np.zeros(len(messages), bool), np.zeros(
                len(incoming_ids), bool
            )
            mask_x[x_ind], mask_y[y_ind] = True, True

            # update no_shares and age of existing messages
            no_shares[mask_x] += incoming_shares[mask_y]

            # add age to all existing messages
            ages += np.ones(len(ages), dtype=int)
            # # reset age overlapping messages
            # ages[mask_x] = np.zeros(len(y_ind))

            if self.debug:
                self.logger.debug(
                    f"   after:  messages: {messages}, shares: {no_shares}, ages: {ages}"
                )
            # push new messages into the feed (only the non-overlapping messages)
            no_shares = np.insert(no_shares, 0, incoming_shares[~mask_y])
            messages = np.insert(messages, 0, incoming_ids[~mask_y])
            ages = np.insert(ages, 0, np.zeros(len(incoming_shares[~mask_y])))
            if self.debug:
                self.logger.debug(
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
            sorted_messages[: self.sigma],
            sorted_shares[: self.sigma],
            sorted_ages[: self.sigma],
        )

        assert len(updated_feed[0]) <= self.sigma
        # for i in updated_feed:
        #     assert isinstance(i, np.ndarray)
        return updated_feed

    def _return_all_message_info(self):
        """
        Combine message attributes (quality, appeal) with popularity data (spread_via_agents, seen_by_agents, etc.)
        Return a list of dict, where each dict contains message metadata
        """
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

        # "seen_by_agents" and "seen_by_agent_timestep" are equal-length lists. Used to construct the exposure cascade
        for message_id in feed:
            self.message_metadata[message_id]["seen_by_agents"] += [agent["uid"]]
            self.message_metadata[message_id]["seen_by_agent_timestep"] += [
                self.time_step
            ]

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
                "seen_by_agent_timestep": [],
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
                f" - converge_by: {self.converge_by} - keep running while: {self.converge_condition} - max_steps:{self.max_steps}"
                f"\nPropagation parameters:",
                f" - mu (posting rate): {self.mu}",
                f" - sigma (feedsize):  {self.sigma}",
                f"Network contains one type of agents (no bots): {self.is_human_only}",
                f"{bot_params}",
            ]
        )
