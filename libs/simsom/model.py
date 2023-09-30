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
    - phi (int): phi*0.1 is the probability that a bot message's engagement (engagment) equals 1. Default: 0
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
            - phi (int): same as phi specified in InfoSys
            - quality (float): quality
            - engagement (float): engagement 
            - human_shares (int): number of shares by humans
            - bot_shares (int): number of shares by bots
            - spread_via_agents (list): list of uids of agents who reshared this message
            - seen_by_agents (list): list of uids of agents who are exposed to this message (disregard bot spam)
            - infeed_of_agents (list): list of uids of agents who are exposed to this message (including bot spam)
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
        epsilon=0.0001,  # Don't change this value
        rho=0.8,  # Don't change this value, check note above
        mu=0.5,
        phi=0,
        alpha=15,
        theta=1,
    ):
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
            self.agent_feeds = defaultdict(lambda: ([], []))
            if verbose is True:
                # sanity check: calculate number of followers
                in_deg = [self.network.degree(n, mode="in") for n in self.network.vs]
                print(
                    "Graph Avg in deg", round(sum(in_deg) / len(in_deg), 2), flush=True
                )

        except Exception as e:
            print(
                f"Unable to read graph file. File doesn't exist of corrupted: {graph_gml}",
                flush=True,
            )
            print(e, flush=True)

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
            num_messages = sum([len(feed) for feed, _ in self.agent_feeds.values()])
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

            all_agents = self.network.vs

            # Propagate messages
            self.simulation_step(all_agents)

            self.update_quality()

        # return feeds, self.message_metadata, self.quality
        # Call this before calculating tau and diversity!!
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
            measurements["all_messages"] = self.message_dict
            measurements["all_feeds"] = self.agent_feeds

        return measurements

    def simulation_step(self, all_agents):
        """
        During each simulation step, each agent reshare or post new messages (this process is performed in parallel for `n` agents).
        This step represents the distribution of messages by the platform to various feeds.
        Inputs:
            - all_agents (list): list of agent ids
        """
        ##TODO: update docstring
        # Following the resharing or posting of messages by all agents, there are often cases where multiple friends attempt to modify the same newsfeed within the same timestep.
        # In such cases, the platform consolidates these feeds by randomly selecting new messages from one of the friends. The chosen message is then posted onto the respective agent's feed.
        q = queue.Queue()

        def post_message(agent):
            modify_requests = self.user_step(agent)
            if len(modify_requests) > 0:
                q.put(modify_requests)

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(post_message, all_agents)
            if self.time_step == 1:
                print(
                    f" - Simulation running on {executor._max_workers} threads",
                    flush=True,
                )
        update_list = defaultdict(lambda: defaultdict(int))

        # Distribute posts to newsfeeds
        # each item in queue is a list of requests from an agent to modify its follower feeds
        # e.g.: item= [(follower1, [mess1]), (follower2, [mess1]), .. ]
        # or item= [(follower1, [mess1]*theta), (follower2, [mess1]*theta), .. ] if the agent is a bot
        # use requests from friends to add messages to agents' feeds
        # find overlaps between friends' message lists to update popularity
        for item in q.queue:
            for agent_id, message_ids in item:
                for message_id in message_ids:
                    update_list[agent_id][message_id] += 1
        # eg:
        # {'a1': defaultdict(int, {'1': 4, '2': 1, '3': 1, '6': 1, '7': 1}),
        # 'a2': defaultdict(int, {'2': 1, '1': 1, '4': 1})}
        # print("Update list:", update_list, flush=True)

        # update_list: {agent_id: {message_id: count}}
        for agent_id, message_list in update_list.items():
            message_ids = list(message_list.keys())
            popularity = list(message_list.values())
            self._bulk_add_messages_to_feed(agent_id, message_ids, popularity)

        # print("Agent feeds after updating:", self.agent_feeds, flush=True)

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

        agent_id = agent["uid"]
        feed, popularity = self.agent_feeds[agent_id]

        # update agent exposure to messages in its feed at login
        self._update_exposure(feed, agent)

        # posting
        message_id = self._create_post(agent)
        # book keeping (for all messages)
        self._update_message_popularity(message_id, agent)

        # spread: make requests to add message to top of follower's feed (theta copies if poster is bot to simulate flooding)
        follower_idxs = self.network.predecessors(agent)  # return list of int
        follower_uids = [n["uid"] for n in self.network.vs if n.index in follower_idxs]

        modify_requests = []

        for follower in follower_uids:
            try:
                if self.output_cascades is True:
                    self._update_reshares(message_id, agent_id, follower)

                if agent["bot"] == True:
                    modify_requests.append((follower, [message_id] * self.theta))
                else:
                    modify_requests.append((follower, [message_id]))
            except Exception as e:
                print(e, flush=True)
                sys.exit(
                    "Error while updating tracking/appending to modify_requests (user_step)."
                )

        return modify_requests

    def _create_post(self, agent):
        """
        Create a new message or reshare a message from newsfeed
        Returns a message id (int)
        """
        # TODO: Do we want to keep the popularity of messages at each timestep?
        # Or keep a copy of agent's feed (message-popularity) for each timestep?

        try:
            agent_id = agent["uid"]
            feed, popularity = self.agent_feeds[agent_id]
            feed_messages = [self.all_messages[message_id] for message_id in feed]
            # return messages created by the agent via resharing or posting
            if len(feed) > 0 and random.random() > self.mu:
                # retweet a message from feed selected on basis of its engagement and popularity
                # Note: random.choices() weights input doesn't have to be normalized
                engagement = [message.engagement for message in feed_messages]
                ranking = np.multiply(engagement, popularity)

                (message,) = random.choices(feed_messages, weights=ranking, k=1)
            else:
                # new message
                self.num_message_unique += 1
                message = Message(
                    id=self.num_message_unique,
                    is_by_bot=agent["bot"],
                    phi=self.phi,
                )

                self.all_messages[message.id] = message
        except Exception as e:
            print(e)
            raise ValueError("Failed to create a new message.")
        return message.id

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
            message_ids, _ = self.agent_feeds[u]
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
            message_ids, _ = feed
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

    def _bulk_add_messages_to_feed(self, target_id, message_ids, popularity):
        """
        Add message to agent's feed in bulk, forget the oldest if feed size exceeds self.alpha (Last in last out)
        Update all news feed information if output_cascades is True
        Return a copy of the target agent's feed after modification
        Input:
        - target_id (str): uid of agent resharing the message -- whose feed we're adding the message to
        - message_ids (list of ints): ids of messages to add
        - popularity (list of int): popularity of each message. Popularity[i] is the popularity of message i
        Note: feed[0] is the most recent item in the newsfeed
        """
        messages, metadata = deepcopy(self.agent_feeds[target_id])
        messages[0:0] = message_ids
        metadata[0:0] = popularity

        newsfeed = (messages, metadata)

        # clip the agent's feed if exceeds alpha
        if len(message_ids) > self.alpha:
            newsfeed = self._handle_oversized_feed(newsfeed)
        self.agent_feeds[target_id] = newsfeed

        return

    def _handle_oversized_feed(self, newsfeed):
        """
        Handles oversized newsfeed and message extinction
        Returns the newsfeed (tuple of lists) where the oldest message is removed
        Input:
            feed (tuple - (list of int, list of int)): (list of mess_ids - list of popularities), represents an agent's news feed
        """
        message_ids, metadata = deepcopy(newsfeed)
        updated_feed = (message_ids[: self.alpha], metadata[: self.alpha])

        # b: We don't want to remove forgotten messages (because we need to keep track of their exposure cascade)
        # # Extinction: remove oldest (forgotten) messages from master lists
        # for message_id in set(message_ids[self.alpha :]):
        #     _ = self.message_metadata.pop(message_id, "No Key found")
        #     _ = self.all_messages.pop(message_id, "No Key found")

        return updated_feed

    def _return_all_message_info(self):
        for message in self.all_messages.values():
            assert isinstance(message, Message)
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
            self.message_metadata[message_id] = {
                "agent_id": agent["uid"],
                # "is_by_bot": message.is_by_bot,
                "human_shares": 0,
                "bot_shares": 0,
                "spread_via_agents": [],
                "seen_by_agents": [],  # disregard bot spam
                "infeed_of_agents": [],  # regard bot spam
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
