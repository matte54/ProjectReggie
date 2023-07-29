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
        # set these modifiers to use to enhance to de-hance casts
        self.fail_rate_modifier = 0.0   # negative numbers increase chance(max pos/neg is 5)
        self.class_modifier = 0
        self.rarity_modifier = 0.0
        # constant stuff
        self.client = client
        self.profile_dir = "./local/fishing/profiles/"
        self.database_dir = "./data/fishing/databases/"
        self.fish_databases = ["class1.json", "class2.json", "class3.json", "class4.json", "class5.json", "class6.json", "class7.json"]

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
        self.rolls()

    def rolls(self):
        now = datetime.datetime.now()
        self.user_profile["last"] = str(now.isoformat())  # update the last cast time
        self.write_json(f"{self.profile_dir}{self.user_id}.json", self.user_profile)  # this should probably be moved to the end of the function later to reduce writing

        # class pick
        chosen_class = random.choices(self.fish_databases, weights=WEIGHTS["default"])
        # this aint pretty but it gets u the correct file with the modifier
        index_of_item = self.fish_databases.index(chosen_class[0])
        index_of_item = index_of_item + self.class_modifier
        final_item = self.fish_databases[index_of_item]

        with open(f'{self.database_dir}{final_item}', "r") as f:
            data = json.load(f)

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

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        if debug_on():
            log(f'[Fishing] - Wrote {filepath}')
