import datetime
import random
import json
import os

from systems.logger import debug_on, log
from data.fishing.flare import FLARE, NAMEDFLARE
from data.fishing.weights import WEIGHTS


class Fishing:
    def __init__(self, client):
        self.user_profile_path = None
        self.user_profile = None
        self.user_id = None
        self.message = None
        self.caught_fish = None
        # set these modifiers to use to enhance to de-hance casts
        self.fail_rate_modifier = 0.0  # negative numbers increase chance(max pos/neg is 5)
        self.class_modifier = 0
        self.rarity_modifier = 0.0
        # constant stuff
        self.client = client
        self.profile_dir = "./local/fishing/profiles/"
        self.database_dir = "./data/fishing/databases/"
        self.bucket_dir = "./local/fishing/buckets/"
        self.fish_databases = ["class1.json", "class2.json", "class3.json", "class4.json", "class5.json", "class6.json",
                               "class7.json"]

    async def cast(self, message):
        self.message = message
        self.user_id = message.author.id  # int
        self.user_profile, self.user_profile_path = self.get_profile(self.user_id)  # return profile dict and path(str)

        if await self.spam_check():  # check if casted within a minute
            return

        # fail check
        self.between_casts()  # lower or raise failchance based on time since last
        if await self.failed():
            if debug_on():
                log(f'[Fishing] - User failed cast')
            return
        # so when we reached this far we are guaranteed a fish so now for the rolls
        # trying to build a rolling function that can take all modifiers in consideration
        # and also future modifiers , so figureing out something here is key

        self.rolls()  # do all the rolling and randoming to picka a fish
        self.handle_bucket()  # add fish to bucket

    def rolls(self):
        now = datetime.datetime.now()
        self.user_profile["last"] = str(now.isoformat())  # update the last cast time
        self.write_json(f"{self.profile_dir}{self.user_id}.json",
                        self.user_profile)  # this should probably be moved to the end of the capture process

        # class pick
        chosen_class = random.choices(self.fish_databases, weights=WEIGHTS["default"])
        # this aint pretty but it gets u the correct file with the modifier
        index_of_item = self.fish_databases.index(chosen_class[0])
        index_of_item = index_of_item + self.class_modifier
        final_item = self.fish_databases[index_of_item]

        with open(f'{self.database_dir}{final_item}', "r") as f:
            data = json.load(f)
        # random a fish (this needs the rarity modifier implementation)
        fish = random.choice(list(data))
        self.caught_fish = data[fish]  # get dictionary with all data regarding caught fish
        self.caught_fish["name"] = fish  # add in the fish name, just to have everything in the same dict
        # get fish weight with triangular random to weight towards the middle
        half_weight = (self.caught_fish["min_weight"] + self.caught_fish["max_weight"]) / 2
        fish_weight = round(
            random.triangular(self.caught_fish["min_weight"], self.caught_fish["max_weight"], half_weight), 2)
        weightCategory = self.weight_category(self.caught_fish["min_weight"], self.caught_fish["max_weight"],
                                              fish_weight)
        # add in the stuff into the fish dict for easy keeping
        self.caught_fish["weight"] = fish_weight
        self.caught_fish["category"] = weightCategory

    def between_casts(self):
        time_difference = datetime.datetime.now() - datetime.datetime.fromisoformat(self.user_profile["last"])
        # linear interpolation for lower chance (pretty proud of dis LUL)
        seconds_between_casts = int(time_difference.total_seconds())
        if seconds_between_casts < 3600:
            result = 5.0 + (0.0 - 5.0) * (seconds_between_casts / 3600)
            self.fail_rate_modifier = result
        if seconds_between_casts > 3600:
            result = 5.0 + (0.0 - 5.0) * (seconds_between_casts / 43200)
            self.fail_rate_modifier -= result
            class_result = 0 - (0 - 3) * (seconds_between_casts / 43200)
            self.class_modifier = class_result
        # this might need some smaller re-evalution when levels and other modifiers get into the mix

    async def spam_check(self):
        # check here if cast was less then a minute ago
        if not self.user_profile["last"]:  # this is fix for if the profile is newly created and has no last cast
            return False
        last_cast = datetime.datetime.fromisoformat(self.user_profile["last"])
        time_difference = datetime.datetime.now() - last_cast
        if time_difference < datetime.timedelta(seconds=60):
            await self.message.channel.send(
                f'```yaml\nYou are not allowed to fish again this soon {self.message.author}!```')
            return True
        else:
            return False

    async def failed(self):
        # rolls to check for success this needs more modifiers for items and other stuff later
        # but for now i will use the same as 1.0
        roll = random.uniform(3.0 + (0.025 * self.user_profile["level"]), 10)
        # print(f'fail roll was {roll} and it needs to be bigger then {5 + self.fail_rate_modifier}')
        if roll < (5 + self.fail_rate_modifier):
            await self.message.channel.send(
                f'```yaml\n{self.message.author} casts their line but {random.choice(FLARE)}```')
            # add last cast time in
            now = datetime.datetime.now()
            self.user_profile["last"] = str(now.isoformat())  # update the last cast time
            self.write_json(f"{self.profile_dir}{self.user_id}.json", self.user_profile)
            if debug_on():
                log(f'[Fishing] - {self.message.author} failed cast')
            return True
        else:
            return False

    def get_profile(self, user_id):
        # if profile exists load and return
        if os.path.isfile(f"{self.profile_dir}{user_id}.json"):
            with open(f"{self.profile_dir}{user_id}.json", "r") as f:
                data = json.load(f)
            return data, f"{self.profile_dir}{user_id}.json"
        # if it does not, create AND return
        else:
            data = {
                "money": 0,
                "xp": 0,
                "xpCap": 10,
                "level": 1,
                "gear": [],
                "last": ""
            }
            log(f'[Fishing] - {self.message.author} has no fishing profile, creating...')
            self.write_json(f"{self.profile_dir}{user_id}.json", data)
            return data, f"{self.profile_dir}{user_id}.json"

    def handle_profile(self):
        pass

    def handle_bucket(self):
        now = datetime.datetime.now()
        # if the bucket does not exist create and add fish
        if not os.path.isfile(f"{self.bucket_dir}{self.user_id}.json"):
            data = {
                self.caught_fish["name"]:
                    {
                        "weight": self.caught_fish["weight"],
                        "worth": self.caught_fish["value"],
                        "unique": self.caught_fish["unique"],
                        "time": str(now.isoformat())
                    }
            }
            self.write_json(f"{self.bucket_dir}{self.user_id}.json", data)
        else:
            # add fish to existing bucket
            with open(f"{self.bucket_dir}{self.user_id}.json", "r") as f:
                data = json.load(f)

            if self.caught_fish["name"] in data:
                print("User already have this fish")
                # do stuff selling etc
                return
            data[self.caught_fish["name"]] = {}
            data[self.caught_fish["name"]]["weight"] = self.caught_fish["weight"]
            data[self.caught_fish["name"]]["worth"] = self.caught_fish["value"]
            data[self.caught_fish["name"]]["unique"] = self.caught_fish["unique"]
            data[self.caught_fish["name"]]["time"] = str(now.isoformat())

            self.write_json(f"{self.bucket_dir}{self.user_id}.json", data)

    def weight_category(self, w_l, w_h, w):
        # this weight category is directly imported from 1.0
        x = 0
        sizes = ['', 'tiny', 'small', 'medium', 'large', 'big', 'huge']
        stops = []
        difference = w_h - w_l
        stage_range = difference / 7
        for i in range(1, 7):
            stop = stage_range * i + w_l
            stops.append(stop)
        for y in stops:
            x += 1
            if y > w:
                o = y
                break
        return sizes[x]

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        if debug_on():
            log(f'[Fishing] - Wrote {filepath}')
