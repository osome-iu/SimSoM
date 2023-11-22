"""
Class modeling a message. 
Quality: Exponential 
Appeal: Powerlaw
"""
import random
import numpy as np


class Message4pl:
    def __init__(self, id, is_by_bot=0, phi=0):
        """
        Initializes an instance for a message.
        Quality and engagement values are decided by the parameter phi.
        Parameters:
            - id (int): unique identifier for this message
            - is_by_bot (int): 1 if the message is by bot, else 0
            - phi (float): range [0,1].
            If phi=0, there is no engagement advantage to messages by bot. Meaning engagement of bot and human messages drawn from the same distribution
        """

        self.id = id
        self.is_by_bot = is_by_bot
        self.phi = phi
        quality, engagement = self.get_values()
        self.quality = quality
        self.engagement = engagement  # referred to as "engagement" in the paper

    def expon_quality(self, lambda_quality=-5):
        """
        Return a quality value x, $f(x) \sim Ce^{-\lambda x}$, 0<=x<=1
        $C = \frac{\lambda}{1-e^{-\lambda}}$
        """
        # inverse transform sampling
        x = random.random()
        return np.log(1 - x + x * np.e ** (-1 * lambda_quality)) / (-1 * lambda_quality)

    def pl_appeal(self, appeal_gamma=-2):
        """
        Return an appeal value x following a bounded powerlaw x ~ x^-(appeal_gamma), 0<=x<=1
        http://up-rs-esp.github.io/bpl/
        """
        x = random.random()
        xmin = 0
        xmax = 1
        # generate power law distributed on (xmin, inf)
        # xmin * x ** (-1 / (appeal_gamma- 1))
        a = xmin ** (1 - appeal_gamma)
        b = xmax ** (1 - appeal_gamma) - a
        return (a + b * x) ** (1 / (1 - appeal_gamma))

    def get_values(self):
        """
        Returns (quality, engagement) values of a message based on lowq_prob and phi
        Use inverse transform sampling to draw values from a distribution https://en.wikipedia.org/wiki/Inverse_transform_sampling
        Note that the 2 random numbers generated below may or may not include 1, see https://docs.python.org/3/library/random.html#random.uniform.
            For systems with bots, bot message is fixed to lowq_prob=1, so we don't need to worry about it.
        """

        # engagement value of a "normal" message by humans
        human_engagement = self.pl_appeal()

        u = random.random()
        if self.is_by_bot:
            engagement = 1 if u < self.phi else human_engagement
        else:
            engagement = human_engagement

        if self.is_by_bot:
            quality = 0
        else:
            quality = self.expon_quality()

        return quality, engagement
