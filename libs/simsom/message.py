"""
Class modeling a message. 
"""
import random


class Message:
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

    def get_values(self):
        """
        Returns (quality, engagement) values of a message based on lowq_prob and phi
        Use inverse transform sampling to draw values from a distribution https://en.wikipedia.org/wiki/Inverse_transform_sampling
        Note that the 2 random numbers generated below may or may not include 1, see https://docs.python.org/3/library/random.html#random.uniform.
            For systems with bots, bot message is fixed to lowq_prob=1, so we don't need to worry about it.
        """

        u = random.random()
        exponent = 2
        # engagement value of a "normal" message by humans
        human_engagement = 1 - (1 - u) ** (1 / exponent)

        if self.is_by_bot:
            engagement = 1 if u < self.phi else human_engagement
        else:
            engagement = human_engagement

        if self.is_by_bot:
            quality = 0
        else:
            quality = engagement

        return quality, engagement
