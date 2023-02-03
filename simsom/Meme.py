"""
Class modeling a message. 
"""
import random


class Meme:
    def __init__(self, id, is_by_bot=0, phi=0):
        """
        Initializes an instance for a message.
        Quality and fitness values are decided by the parameter phi.
        Parameters:
            - id (int): unique identifier for this message
            - is_by_bot (int): 1 if the message is by bot, else 0
            - phi (float): range [0,1]. 
            If phi=0, there is no engagement advantage to messages by bot. Meaning engagement of bot and human messages drawn from the same distribution
        """

        self.id = id
        self.is_by_bot = is_by_bot
        self.phi = phi
        quality, fitness = self.get_values()
        self.quality = quality
        self.fitness = fitness  # referred to as "engagement" in the paper

    def get_values(self):
        # return (quality, fitness) values of a message based on phi and bot flag
        # Use inverse transform sampling to draw values from a distribution
        # https://en.wikipedia.org/wiki/Inverse_transform_sampling

        u = random.random()
        exponent = 2
        human_fitness = 1 - (1 - u) ** (1 / exponent)

        if self.is_by_bot == 1:
            fitness = 1 if u < self.phi else human_fitness
        else:
            fitness = human_fitness

        if self.is_by_bot == 1:
            quality = 0
        else:
            quality = fitness

        return quality, fitness
