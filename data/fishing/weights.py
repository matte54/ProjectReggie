# school weights
import random

WEIGHTS = {"default": [38, 19, 15, 12, 7, 6, 3],
           "class2": [19, 38, 15, 12, 7, 6, 3],
           "class3": [15, 19, 38, 12, 7, 6, 3],
           "class4": [7, 15, 19, 38, 12, 6, 3],
           "class5": [3, 6, 12, 19, 38, 15, 7],
           "class6": [3, 6, 7, 12, 19, 38, 15],
           "class7": [3, 6, 7, 12, 15, 19, 38],
           "trip": [random.randint(1, 38), random.randint(1, 38), random.randint(1, 38), random.randint(1, 38),
                        random.randint(1, 38), random.randint(1, 38), random.randint(1, 38)]
           }
