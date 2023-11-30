"""
Class modeling a message. 
A message has 2 intrinsic, independent attributes:
- Quality following an exponential distribution (estimated using empirical data)
- Appeal, following a right-skewed distribution
"""
import random
import numpy as np


class Message:
    def __init__(self, id, is_by_bot=0, phi=0, appeal_exp=5):
        """
        Initializes an instance for a message.
        Quality and appeal values are decided by the parameter phi.
        Parameters:
            - id (int): unique identifier for this message
            - is_by_bot (int): 1 if the message is by bot, else 0
            - phi (float): range [0,1].
            - appeal_exp (int): exponent alpha characterizes the rarity of high appeal values are
            If phi=0, there is no appeal advantage to messages by bot. Meaning appeal of bot and human messages drawn from the same distribution
        """

        self.id = id
        self.is_by_bot = is_by_bot
        self.phi = phi
        self.appeal_exp = appeal_exp
        quality, appeal = self.get_values()
        self.quality = quality
        self.appeal = appeal

    def expon_quality(self, lambda_quality=-5):
        """
        Return a quality value x via inverse transform sampling
        Pdf of quality: $f(x) \sim Ce^{-\lambda x}$, 0<=x<=1
        $C = \frac{\lambda}{1-e^{-\lambda}}$
        """
        x = random.random()
        return np.log(1 - x + x * np.e ** (-1 * lambda_quality)) / (-1 * lambda_quality)

    def appeal_func(self, exponent=5):
        """
        Return an appeal value a following a right-skewed distribution via inverse transform sampling
        Pdf of appeal: $P(a) = (1+\alpha)(1-a)^{\alpha}$, the larger alpha, the more skewed the distribution is
        exponent = alpha+1
        """
        if self.id == 1:
            print(f"Created message using appeal exp alpha={self.appeal_exp}")
        u = random.random()
        return 1 - (1 - u) ** (1 / exponent)

    def get_values(self):
        """
        Returns (quality, appeal) values for messages based on phi
        Use inverse transform sampling to draw values from a distribution https://en.wikipedia.org/wiki/Inverse_transform_sampling
        """

        # appeal value of a "normal" message by humans
        human_appeal = self.appeal_func(exponent=self.appeal_exp)

        u = random.random()
        if self.is_by_bot:
            appeal = 1 if u < self.phi else human_appeal
        else:
            appeal = human_appeal

        if self.is_by_bot:
            quality = 0
        else:
            quality = self.expon_quality()

        return quality, appeal
