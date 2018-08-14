import itertools

COLORS = ["white", "blue", "orange", "black", "yellow", "green", "red", "taupe"]
ADJ = ["flippant", "dashing", "sullen", "starving", "ravishing",
       "sickly", "gaunt", "spry", "homely", "greasy"]
NOUNS = ["condor", "triangle", "notebook", "shovel",
         "hairbrush", "boots", "clarinet"]


def names():
    return itertools.product(COLORS, ADJ, NOUNS)
