""" 
Code to (re)produce results in the paper 
"Manipulating the Online Marketplace of Ideas" (Lou et al.)
https://arxiv.org/abs/1907.06130

Main class to run the simulation. Represents an Information System

Inputs: 
    - graph_gml (str): path to igraph .graphml file
    - tracktimestep (bool): if True, track overall quality at each timestep 
    - save_memeinfo (bool): if True, save all meme and news feeds info (popularity, mapping of feed-memes, etc. this info is still tracked if flag is False)
    - output_cascades (bool): if True, track & save reshares and exposures to .csv files (for network viz)
    - verbose (bool): if True, print messages 
    - epsilon (float): threshold of quality difference between 2 consecutive timesteps to decide convergence. Default: 0.0001
    - rho (float): weight of the previous timestep's quality in calculating new quality. Default: 0.8
    - mu (float): probability that an agent create new memes. Default: 0.5
    - phi (int): phi*0.1 is the probability that a bot meme's fitness equals 1. Default: 0
    - alpha (int): agent's feedsize. Default: 15
    - theta (int): number of copies bots make when creating memes. Default: 1
Important note: 
    - graph_gml: link direction is following (follower -> friend), opposite of info spread!
    - Epsilon value was tested and fixed to the default values above.
        to ensure convergence on the empirical network or network with >=10000 nodes:
            - epsilon <= 0.0001
            - rho >= 0.5
Outputs:
    - measurements (dict): results and information tracked during the simulation. The fields are:
        - quality (float): average quality of all memes from a humans' feeds.
        - diversity (float): entropy calculated from all meme's quality
        - discriminative_pow (list): results of the Kendall's correlation coefficient test: [tau, p-value]
        - quality_timestep (list of dict): quality of the system over time 
        - all_memes (list of dict): each dictionary contains the meme's information. Dict keys are:
            - id (int): unique identifier for this meme
            - agent_id (str): uid of agent originating this meme
            - is_by_bot (int): 0 if meme is by human, 1 if by bot
            - phi (int): same as phi specified in InfoSys
            - quality (float): quality
            - fitness (float): engagement 
            - human_shares (int): number of shares by humans
            - bot_shares (int): number of shares by bots
            - spread_via_agents (list): list of uids of agents who reshared this meme
            - seen_by_agents (list): list of uids of agents who are exposed to this meme (disregard bot spam)
            - infeed_of_agents (list): list of uids of agents who are exposed to this meme (including bot spam)
            - qual_th (int): quality ranking
            - share_th (int): popularity ranking
        - all_feeds (dict): dictionary mapping agent's feed to the memes it contains at convergence
            Structure: {agent_id (str): meme ids(list)} 
            - agent_id (str): uid -- unique identifier of an agent (different from vertex id)
        - reshares (list of dict): each dict is a reshare edge. The keys are:
            - meme_id (int): unique identifier of a meme
            - timestep (int): timestamp of the reshare
            - agent1 (str): uid of the agent spreading the meme
            - agent2 (str): uid of the agent resharing the meme
"""

from simsom import MessageV2
import simsom.utils as utils
import igraph as ig
import csv
import random
import numpy as np
from collections import Counter


class SimSomV2:
    def __init__(
        self,
        graph_gml,
        tracktimestep=True,
        save_memeinfo=True,
        output_cascades=False,
        verbose=False,
        epsilon=0.0001,  # Don't change this value
        rho=0.8,  # Don't change this value, check note above
        mu=0.5,
        phi=0,
        alpha=15,
        theta=1,
        logger=None,
    ):
        print("SimSomV2")

        self.graph_gml = graph_gml
        self.verbose = verbose
        self.tracktimestep = tracktimestep
        self.save_memeinfo = save_memeinfo
        self.output_cascades = output_cascades
        self.quality_timestep = []
        self.epsilon = epsilon
        self.rho = rho
        self.mu = mu
        self.phi = phi
        self.alpha = alpha
        self.theta = theta

        ## Debugging
        self.random_seed = 10
        random.seed(self.random_seed)
        self.logger = logger

        # Keep track of number of memes globally
        self.meme_dict = []
        self.all_memes = []  # list of Meme objects

        self.num_message_unique = 0
        self.num_human_messages = 0  # number of messages across all human feeds
        # number of unique messages across all human feeds
        self.num_human_messages_unique = 0

        # self.num_memes = 0  # for verbose debug
        # self.num_meme_unique = 0  # for verbose debug
        # self.memes_human_feed = 0  # for verbose debug
        self.quality_diff = 1
        self.quality = 1
        self.time_step = 0

        self.meme_popularity = {}
        try:
            self.network = ig.Graph.Read_GML(self.graph_gml)
            if verbose is True:
                self.logger.info(self.network.summary())

            self.n_agents = self.network.vcount()
            # init an empty feed for all agents
            self.agent_feeds = {agent["uid"]: [] for agent in self.network.vs}

            if verbose is True:
                # sanity check: calculate number of followers
                in_deg = [self.network.degree(n, mode="in") for n in self.network.vs]
                self.logger.info(
                    "Graph Avg in deg", np.round(sum(in_deg) / len(in_deg), 2)
                )

        except Exception as e:
            self.logger.error(
                f"Unable to read graph file. File doesn't exist of corrupted: {graph_gml}"
            )
            self.logger.error(e)

    def simulation(self, reshare_fpath="", exposure_fpath=""):
        """
        Driver for simulation.
        This function calls simulation_step() N times at each timestep (where N is number of agents).
        It then updates the overall quality at each timestep and checks for convergence
        Inputs (optional):
            - reshare_fpath: path to .csv file containing reshare cascade info
            - exposure_fpath: path to .csv file containing exposure cascade info
        """
        if self.output_cascades is True:
            self.reshare_fpath = reshare_fpath
            reshare_fields = ["meme_id", "timestep", "agent1", "agent2"]
            with open(self.reshare_fpath, "w", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(reshare_fields)

            self.exposure_fpath = exposure_fpath
            exposure_fields = ["agent_id", "meme_id", "reshared_by_agent", "timestep"]
            with open(self.exposure_fpath, "w", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(exposure_fields)

        while self.quality_diff > self.epsilon:
            num_messages = sum([len(f) for f in self.agent_feeds.values()])
            if self.verbose:
                self.logger.info(
                    f"- time_step = {self.time_step}, q = {np.round(self.quality, 5)}, diff = {np.round(self.quality_diff, 6)}, existing human/all messages: {self.num_human_messages}/{num_messages}, unique human messages: {self.num_human_messages_unique}, total created: {self.num_message_unique}"
                )

            self.time_step += 1
            if self.tracktimestep is True:
                self.quality_timestep += [self.quality]

            # all_agents = random.choice(self.network.vs)

            for _ in range(self.n_agents):
                # simulation

                self.simulation_step()

            self.update_quality()

        # return feeds, self.meme_popularity, self.quality
        # Call this before calculating tau and diversity!!
        self.meme_dict = self._return_all_meme_info()

        measurements = {
            "quality": self.quality,
            "diversity": self.measure_diversity(),
            "discriminative_pow": self.measure_kendall_tau(),
        }

        if self.save_memeinfo is True:
            # Save feed info of agent & meme popularity
            all_feeds = self.agent_feeds

            feeds = {}
            for agent, memelist in all_feeds.items():
                # convert self.agent_feed into dict of agent_uid - [meme_id]
                feeds[agent] = [meme.id for meme in memelist]

            measurements["quality_timestep"] = self.quality_timestep
            measurements["all_memes"] = self.meme_dict
            measurements["all_feeds"] = feeds

        return measurements

    def simulation_step(self):
        """
        A simulation step: An agent is chosen at random. The chosen agent can reshare or post a new message.
        Keep track of message reshare and exposure information if output_cascades is True.
        """
        agent = random.choice(self.network.vs)
        agent_id = agent["uid"]
        feed = self.agent_feeds[agent_id]

        if len(feed) > 0 and random.random() > self.mu:
            # retweet a meme from feed selected on basis of its fitness
            (meme,) = random.choices(feed, weights=[m.fitness for m in feed], k=1)
        else:
            # new meme
            self.num_message_unique += 1
            meme = MessageV2(
                self.num_message_unique, is_by_bot=agent["bot"], phi=self.phi
            )

            self.all_memes += [meme]

        # book keeping
        self._update_meme_popularity(meme, agent)
        self._update_exposure(feed, agent)

        # spread (truncate feeds at max len alpha)
        follower_idxs = self.network.predecessors(agent)  # return list of int
        follower_uids = [n["uid"] for n in self.network.vs if n.index in follower_idxs]

        self.logger.info(f"   {agent_id} posts {meme.id} to followers {follower_uids}")

        for follower in follower_uids:
            # add meme to top of follower's feed (theta copies if poster is bot to simulate flooding)
            if agent["bot"] == 1:
                self._add_meme_to_feed(
                    target_id=follower,
                    meme=meme,
                    source_id=agent_id,
                    n_copies=self.theta,
                )
            else:
                self._add_meme_to_feed(
                    target_id=follower, meme=meme, source_id=agent_id
                )

            assert len(self.agent_feeds[follower]) <= self.alpha

            if self.output_cascades is True:
                self._update_reshares(meme, agent_id, follower)

        return

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
        (Invoke only after self._return_all_meme_info() is called)
        """

        quality_ranked = sorted(self.meme_dict, key=lambda m: m["quality"])
        for ith, elem in enumerate(quality_ranked):
            elem.update({"qual_th": ith})

        share_ranked = sorted(quality_ranked, key=lambda m: m["human_shares"])
        for ith, elem in enumerate(share_ranked):
            elem.update({"share_th": ith})

        idx_ranked = sorted(share_ranked, key=lambda m: m["id"])
        ranking1 = [meme["qual_th"] for meme in idx_ranked]
        ranking2 = [meme["share_th"] for meme in idx_ranked]
        tau, p_value = utils.kendall_tau(ranking1, ranking2)
        return tau, p_value

    def measure_average_quality(self):
        """
        Calculates the average quality across human memes in system
        """
        total = 0
        count = 0
        # keep track of no. messages for verbose debug
        human_message_ids = []

        human_uids = [n["uid"] for n in self.network.vs if n["bot"] == 0]
        for u in human_uids:
            for meme in self.agent_feeds[u]:
                total += meme.quality
                count += 1

                human_message_ids += [meme.id]

        self.num_human_messages = count
        self.num_human_messages_unique = len(set(human_message_ids))

        return total / count if count > 0 else 0

    def measure_diversity(self):
        """
        Calculates the diversity of the system using entropy (in terms of unique memes)
        (Invoke only after self._return_all_meme_info() is called)
        """
        humanshares = []
        for human, feed in self.agent_feeds.items():
            for meme in feed:
                humanshares += [meme.id]
        meme_counts = Counter(humanshares)
        # return a list of [(memeid, count)], sorted by id
        count_byid = sorted(dict(meme_counts).items())
        humanshares = np.array([m[1] for m in count_byid])

        hshare_pct = np.divide(humanshares, sum(humanshares))
        diversity = utils.entropy(hshare_pct) * -1
        # Note that (np.sum(humanshares)+np.sum(botshares)) !=self.num_memes because a meme can be shared multiple times
        return diversity

    def _add_meme_to_feed(self, target_id, meme, source_id, n_copies=1):
        """
        Add meme to agent's feed, forget the oldeest if feed size exceeds self.alpha (Last in last out)
        Update all news feed information if output_cascades is True
        Input:
        - target_id (str): uid of agent resharing the meme -- whose feed we're adding the meme to
        - meme (Message object): meme being reshared
        - source_id (str): uid of agent spreading the meme
        """

        feed = self.agent_feeds[target_id]

        message_ids = [message.id for message in feed]
        if self.time_step % 5 == 0:
            self.logger.info(f"   {meme.id} --> {target_id}")

            self.logger.info(f"   Before ({target_id}): {message_ids}")
            self.logger.info(f"   Before populr: {dict(Counter(message_ids))}")

        overlap = set(message_ids) & set([meme.id])
        if len(overlap) > 0:
            self.logger.info(f"Overlap: {overlap}..")

        feed[0:0] = [meme] * n_copies

        if self.output_cascades is True:
            self._update_feed_data(target=target_id, meme_id=meme.id, source=source_id)

        if len(feed) > self.alpha:
            # clip the agent's feed if exceeds alpha, update value of the feed in dictionary
            self.agent_feeds[target_id] = self.agent_feeds[target_id][: self.alpha]
            # Remove memes from popularity info & all_meme list if extinct
            for meme in set(self.agent_feeds[target_id][self.alpha :]):
                _ = self.meme_popularity.pop(meme.id, "No Key found")
                self.all_memes.remove(meme)

        message_ids = [message.id for message in self.agent_feeds[target_id]]
        duplicates = [mid for mid, count in Counter(message_ids).items() if count > 1]
        if len(duplicates) > 0:
            self.logger.info(f"Duplicates: {len(duplicates)}..")

        if self.time_step % 10 == 0:
            self.logger.info(f"   After ({target_id}): {message_ids}")
            self.logger.info(f"   After populr: {dict(Counter(message_ids))}")

        return

    def _return_all_meme_info(self):
        for meme in self.all_memes:
            assert isinstance(meme, MessageV2)
        # Be careful: convert to dict to avoid infinite recursion
        memes = [meme.__dict__ for meme in self.all_memes]
        for meme_dict in memes:
            meme_dict.update(self.meme_popularity[meme_dict["id"]])
        return memes

    def _update_reshares(self, meme, source, target):
        """
        Update the reshare cascade information to a file.
        Input:
        - meme (Message object): meme being reshared
        - source (str): uid of agent spreading the meme
        - target (str): uid of agent resharing the meme
        """
        with open(self.reshare_fpath, "a", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow([meme.id, self.time_step, source, target])

        return

    def _update_feed_data(self, target, meme_id, source):
        """
        Concat news feed information to feed information at all time
        (when flag self.output_cascades is True)
        fields: "agent_id", "meme_id", "reshared_by_agent", "timestep"]
        Input:
        - target: agent_id (str): uid of agent being activated
        - meme_id (int): id of meme in this agent's feed
        - source: reshared_by_agent (str): uid of agent who shared the meme
        """

        with open(self.exposure_fpath, "a", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow([target, meme_id, source, self.time_step])

        return

    def _update_exposure(self, feed, agent):
        """
        Update human's exposure to meme whenever an agent is activated (equivalent to logging in)
        (when flag self.output_cascades is True)
        Input:
        - feed (list of Message objects): agent's news feed
        - agent (Graph vertex): agent resharing the meme
        """
        seen = []
        for meme in feed:
            if meme.id not in seen:
                self.meme_popularity[meme.id]["seen_by_agents"] += [agent["uid"]]
            self.meme_popularity[meme.id]["infeed_of_agents"] += [agent["uid"]]
            seen += [meme.id]
        return

    def _update_meme_popularity(self, meme, agent):
        """
        Update information of a meme whenever it is reshared.
        Input:
        - meme (Message object): meme being reshared
        - agent (Graph vertex): agent resharing the meme
        """
        if meme.id not in self.meme_popularity.keys():
            self.meme_popularity[meme.id] = {
                "agent_id": agent["uid"],
                "is_by_bot": meme.is_by_bot,
                "human_shares": 0,
                "bot_shares": 0,
                "spread_via_agents": [],
                "seen_by_agents": [],  # disregard bot spam
                "infeed_of_agents": [],  # regard bot spam
            }

        self.meme_popularity[meme.id]["spread_via_agents"] += [agent["uid"]]

        if agent["bot"] == 0:
            self.meme_popularity[meme.id]["human_shares"] += 1
        else:
            self.meme_popularity[meme.id]["bot_shares"] += self.theta
        return

    def __repr__(self):
        """
        Define the representation of the object.
        """
        return "".join(
            [
                f"<{self.__class__.__name__}() object> constructed from {self.graph_gml}\n",
                f"epsilon: {self.epsilon} -- rho: {self.rho}\n",
                f"mu (posting rate): {self.mu} -- alpha (feedsize): {self.alpha}\n",
                f"phi (deception): {self.phi} -- theta (flooding): {self.theta}\n",
            ]
        )
