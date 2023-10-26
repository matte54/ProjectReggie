import json
import random
import string
import asyncio

from systems.logger import log


class Areamanager:
    def __init__(self):
        # dir paths
        self.areas_dir = "./data/banditlife/areas/"
        self.containers_dir = "./data/banditlife/containers/"
        self.dangers_dir = "./data/banditlife/dangers/"
        self.loot_dir = "./data/banditlife/loot/"
        # lists
        self.areas_list = ["town_1.json"]
        self.square_list = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        self.container_list = ["tier1.json", "tier2.json", "tier3.json", "tier4.json"]

    def restock_loop(self):
        pass

    def reset_loot(self):
        pass

    def random_container(self, container_dict):
        top_level_key = random.choice(list(container_dict.keys()))
        nested_key = random.choice(list(container_dict[top_level_key].keys()))
        container_name = nested_key + "_" + ''.join(random.choices(string.digits, k=4))
        return container_name, container_dict[top_level_key][nested_key]

    def quick_distribute(self):
        # quick distribution only on first startup and or testing
        for area in self.areas_list:
            with open(f'{self.areas_dir}{area}', "r") as f:
                current_area = json.load(f)
            max_stock = current_area["variables"]["stock_max"]
            # container tier strengths
            tier1 = current_area["variables"]["tier1"]
            tier2 = current_area["variables"]["tier2"]
            tier3 = current_area["variables"]["tier3"]
            tier4 = current_area["variables"]["tier4"]

            while current_area["variables"]["stock"] < current_area["variables"]["stock_max"]:
                # add stuff
                square = random.choice(self.square_list)
                roll = random.randint(0, 100)
                if roll > 1:
                    x = random.choices(self.container_list, weights=[tier1, tier2, tier3, tier4])
                    with open(f'{self.containers_dir}{x[0]}', "r") as f:
                        current_container_tier = json.load(f)
                    container_name, picked_container_dict = self.random_container(current_container_tier)
                    current_area[square][container_name] = picked_container_dict
                    current_area["variables"]["stock"] += picked_container_dict["storage"]

            self.write_json(f'{self.areas_dir}{area}', current_area)

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
