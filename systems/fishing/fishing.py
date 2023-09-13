import datetime
import random
import json
import os
import re
import math
from discord import Embed

from systems.logger import debug_on, log
from systems.fishing.fishstats import Fishstat
from data.fishing.flare import FLARE
from data.fishing.weights import WEIGHTS
from systems.varmanager import VarManager

# Modifiers to tweak
SHINYCHANCE = 99  # rolls 1-100 needs to be equals to or greater then the number for shiny


class Fishing:
    def __init__(self, client):
        self.user_profile_path = None
        self.user_profile = None
        self.user_id = None
        self.user_name = None
        self.message = None
        self.channel = None
        self.caught_fish = None
        self.user_bucket = None
        # special modifiers
        self.isShiny = False
        self.isUnique = False
        self.isDing = 0
        self.fishoff_lead_taken = False
        # set these modifiers to use to enhance to de-hance casts
        self.fail_rate_modifier = 0.0  # negative numbers increase chance(max pos/neg is 5)
        self.class_modifier = 0
        self.rarity_modifier = 0.0
        # constant stuff
        self.client = client
        self.fish_stats = Fishstat()
        self.varmanager = VarManager()

        self.profile_dir = "./local/fishing/profiles/"
        self.database_dir = "./data/fishing/databases/"
        self.bucket_dir = "./local/fishing/buckets/"
        self.fish_databases = ["class1.json", "class2.json", "class3.json", "class4.json", "class5.json", "class6.json",
                               "class7.json"]

        self.global_items_list = None
        self.personal_items_list = None

    async def cast(self, message):
        self.caught_fish = None  # reset the fish dict
        self.message = message
        self.user_id = message.author.id  # int
        self.user_name = self.get_user_name(str(self.user_id).capitalize())
        self.channel = message.channel
        self.user_profile, self.user_profile_path = self.get_profile(self.user_id)  # return profile dict and path(str)
        # reset modifiers
        self.fail_rate_modifier = 0.0
        self.class_modifier = 0
        self.rarity_modifier = 0.0

        # reset item lists
        self.global_items_list = []
        self.personal_items_list = []
        # gather current item lists
        self.global_items_list = self.check_global_items()
        self.personal_items_list = self.check_personal_items()

        if await self.spam_check():  # check if casted within a minute
            return
        # fail check
        self.between_casts()  # lower or raise failchance based on time since last

        if await self.failed():
            self.fish_stats.stat_this(self.user_id, None, True, self.isShiny)
            return

        # so when we reached this far we are guaranteed a fish so now for the rolls

        self.rolls()  # do all the rolling and randoming to pick a fish
        # stats
        self.fish_stats.stat_this(self.user_id, self.caught_fish, False, self.isShiny)

        wr, holder = self.wr_check()  # check or create the world record stat

        returnvalue, pb = self.handle_bucket()  # add fish to bucket returns value of sold fish , if new returns None
        if isinstance(returnvalue, int):
            self.handle_money(returnvalue)

        self.fishoff_lead_taken = self.fishoff_handler()  # stuff for fishoff returns True if the fish is the leader

        self.handle_profile()  # do profile stuff

        finished_embed = self.fishing_embed(self.user_name, self.caught_fish["name"], self.caught_fish["joke"],
                                            self.caught_fish["class"], self.caught_fish["weight"],
                                            self.caught_fish["worth"],
                                            self.caught_fish["xp_worth"], self.isShiny, self.isUnique,
                                            self.caught_fish["category"], self.isDing, self.fishoff_lead_taken,
                                            old_pb=pb, old_wr=wr, dethroned=holder)

        self.write_json(f"{self.profile_dir}{self.user_id}.json", self.user_profile)

        await self.channel.send(embed=finished_embed)

    def pick_class(self):
        # class pick
        school_ojb = self.varmanager.read("school")
        if school_ojb[0]:
            end_weights = WEIGHTS[school_ojb[1]]
        else:
            end_weights = WEIGHTS["default"]
        # personal items
        if self.personal_items_list:
            if "sonar" in self.personal_items_list:
                end_weights = [3, 6, 12, 19, 38, 15, 12]
            if "mushroom" in self.personal_items_list:
                end_weights = [random.randint(1, 38), random.randint(1, 38), random.randint(1, 38),
                               random.randint(1, 38),
                               random.randint(1, 38), random.randint(1, 38), random.randint(1, 38)]

        # global items next
        if self.global_items_list:
            if "chum" in self.global_items_list:
                end_weights = [min(x + random.randint(1, 6), 38) for x in end_weights]
                # increase all by 1-6 but not over 38
            if "mirror" in self.global_items_list:
                end_weights.reverse()

        if debug_on():
            # calculate weight percentages instead
            total_weight = sum(end_weights)
            percentage_list = [str(round(((weight / total_weight) * 100))) + "%" for weight in end_weights]
            log(f"[Fishing] - Classweights: {percentage_list}")
        return random.choices(self.fish_databases, weights=end_weights)

    def rolls(self):
        now = datetime.datetime.now()
        self.user_profile["last"] = str(now.isoformat())  # update the last cast time

        chosen_class = self.pick_class()
        # this aint pretty but it gets u the correct file with the modifier
        index_of_item = self.fish_databases.index(chosen_class[0])
        index_of_item = round(index_of_item + self.class_modifier)
        if index_of_item > 6:  # make sure index does not go over 6
            index_of_item = 6
        # DUUH list index starts at 0 making me dizzy
        final_item = self.fish_databases[index_of_item]

        with open(f'{self.database_dir}{final_item}', "r") as f:
            data = json.load(f)

        # testing randoming fish based of rarity value (Not sure how to determain that this works properly)
        # looping for checking if unique and someone has it, it needs to redo. only way i could think of
        decided_fish = False
        while not decided_fish:
            weighted_items = []
            for fish in data:
                weighted_items.append((fish, 'rarity'))
            weights = []
            for fish, key in weighted_items:
                rarity_value = data[fish][key]
                rarity_value -= self.rarity_modifier
                if rarity_value <= 0.0:
                    rarity_value = random.uniform(0.01, 0.18)  # make sure rarity dosent go to low
                weight = 1 / rarity_value
                weights.append(weight)
            fish, key = random.choices(weighted_items, weights=weights, k=1)[0]
            self.caught_fish = data[fish]  # get dictionary with all data regarding caught fish
            # unique checks here
            if self.caught_fish["unique"]:
                # if random.randint(1, 100) > 60:
                #    continue  # unique rate is still to high on 1.0 so put this here MAYBE?
                ucheck = self.unique_checks(fish)
                if ucheck:
                    log(f'[Fishing] - User got unique fish {fish}')
                    self.handle_money(50)  # give the user 50 money for the catch
                    self.isUnique = True
                    decided_fish = True
            else:
                self.isUnique = False
                decided_fish = True

        self.caught_fish["name"] = fish

        # simple shiny system for now
        # this should probably mark the fish in the bucket later not sure if going with astrix thing again
        self.isShiny = False  # reset the shiny status or it will carry over to the next cast
        if random.randint(1, 100) >= SHINYCHANCE:
            self.isShiny = True
            self.caught_fish["min_weight"] *= 2  # double the min weight
            self.caught_fish["max_weight"] *= random.randint(2, 5)  # max weight times 2-5 :/
            self.handle_money(50)

        # get fish weight with triangular random to weight towards the middle
        half_weight = (self.caught_fish["min_weight"] + self.caught_fish["max_weight"]) / 2
        fish_weight = round(
            random.triangular(self.caught_fish["min_weight"], self.caught_fish["max_weight"], half_weight), 2)
        weightcategory, category_number = self.weight_category(self.caught_fish["min_weight"],
                                                               self.caught_fish["max_weight"],
                                                               fish_weight)
        self.caught_fish["class"] = re.findall("\d+", str(final_item))[0]  # class str to an int

        self.caught_fish["weight"] = fish_weight
        self.caught_fish["category"] = weightcategory

        # roll value/xp
        # this adjusts the xp/money value of the fish +/- 3 depending on size for now
        self.caught_fish["worth"] = self.caught_fish["value"]
        self.caught_fish["xp_worth"] = self.caught_fish["xp"]
        if category_number <= 3:
            self.caught_fish["worth"] -= random.randint(1, 3)
            if self.caught_fish["worth"] < 0:
                self.caught_fish["worth"] = 0
            self.caught_fish["xp_worth"] -= random.randint(1, 3)
            if self.caught_fish["xp_worth"] < 0:
                self.caught_fish["xp_worth"] = 0
        else:
            self.caught_fish["worth"] += random.randint(1, 3)
            self.caught_fish["xp_worth"] += random.randint(1, 3)
        log(f"[Fishing] - {self.user_name} caught a {'shiny ' if self.isShiny else ''}"
            f"{self.caught_fish['weight']}lbs {self.caught_fish['name']}")

    def check_global_items(self):
        # find all profiles
        found_global_items = []
        profiles_list = []
        for root, dirs, files in os.walk(self.profile_dir):
            for file in files:
                profiles_list.append(file)
        for profile in profiles_list:
            with open(f'{self.profile_dir}{profile}', "r") as f:
                profiledata = json.load(f)
            if profiledata["gear"]:
                for item in profiledata["gear"]:
                    if item[0] == "chum":
                        found_global_items.append(item[0])
                    if item[0] == "mirror":
                        found_global_items.append(item[0])

        if found_global_items:
            log(f"[Fishing] - {self.user_name} benefits from these global items {found_global_items}")
            return found_global_items
        else:
            return None

    def check_personal_items(self):
        found_personal_items = []
        with open(f'{self.user_profile_path}', "r") as f:
            profiledata = json.load(f)
        if profiledata["gear"]:
            for item in profiledata["gear"]:
                if item[0] != "chum" or item[0] != "mirror":
                    found_personal_items.append(item[0])
        if found_personal_items:
            log(f"[Fishing] - {self.user_name} is using these items {found_personal_items}")
            return found_personal_items
        else:
            return None

    def between_casts(self):
        if not self.user_profile["last"]:  # first cast ever will casue problems if its blank
            return
        time_difference = datetime.datetime.now() - datetime.datetime.fromisoformat(self.user_profile["last"])
        # linear interpolation for lower chance (pretty proud of dis LUL)
        seconds_between_casts = int(time_difference.total_seconds())
        # seconds_between_casts = 10800 # testing
        if seconds_between_casts < 3600:
            result = 5.0 + (0.0 - 5.0) * (seconds_between_casts / 3600)
            self.fail_rate_modifier = result
            self.class_modifier = 0
        if seconds_between_casts > 3600:
            result = 5.0 + (0.0 - 5.0) * (seconds_between_casts / 43200)
            self.fail_rate_modifier += result
            class_result = 0 - (0 - 3) * (seconds_between_casts / 43200)
            self.class_modifier = class_result
        # tacklebox stuff after

        self.item_modifiers()

    def item_modifiers(self):
        if self.personal_items_list:
            if "line" in self.personal_items_list:
                # trying this for now might need tweaks
                self.fail_rate_modifier -= 3
            if "bait" in self.personal_items_list:
                # trying this for now might need tweaks
                self.rarity_modifier += 0.20
        if self.global_items_list:
            if "chum" in self.global_items_list:
                # trying this for now might need tweaks
                self.rarity_modifier += 0.20

    async def spam_check(self):
        # check here if cast was less then a minute ago
        if not self.user_profile["last"]:  # this is fix for if the profile is newly created and has no last cast
            return False
        last_cast = datetime.datetime.fromisoformat(self.user_profile["last"])
        time_difference = datetime.datetime.now() - last_cast
        if time_difference < datetime.timedelta(seconds=60):
            await self.message.channel.send(
                f'```yaml\nYou are not allowed to fish again this soon {self.user_name}!```')
            return True
        else:
            return False

    def unique_checks(self, fish):
        # returns true if no one has the fish
        bucket_list = os.listdir(self.bucket_dir)
        if bucket_list:
            for bucket in bucket_list:
                with open(f'{self.bucket_dir}{bucket}', "r") as f:
                    bucket_data = json.load(f)
                if fish in bucket_data:
                    return False
            return True

    async def failed(self):
        # rolls to check for success this needs more modifiers for items and other stuff later
        # but for now i will use the same as 1.0
        roll = random.uniform(3.0 + (0.025 * self.user_profile["level"]), 10)
        if debug_on():
            # calculate probability.
            total_trials = 10000  # Number of trials to simulate
            successful_trials = 0
            for _ in range(total_trials):
                result = random.uniform(3.0 + (0.025 * self.user_profile["level"]), 10)
                condition = 5 + self.fail_rate_modifier
                if result < condition:
                    successful_trials += 1
            probability = successful_trials / total_trials
            probability_of_success = 1 - probability
            log(f'[Fishing] - Success probability: {probability_of_success:.2%}')

        # print(f'fail roll was {roll} and it needs to be bigger then {5 + self.fail_rate_modifier}')
        if roll < (5 + self.fail_rate_modifier):
            await self.message.channel.send(
                f'```yaml\n{self.user_name} casts their line but FAILS!\n{random.choice(FLARE)}```')
            # add last cast time in
            now = datetime.datetime.now()
            self.user_profile["last"] = str(now.isoformat())  # update the last cast time
            self.write_json(f"{self.profile_dir}{self.user_id}.json", self.user_profile)
            if debug_on():
                log(f'[Fishing] - {self.user_name} failed cast')
            return True
        else:
            return False

    def get_profile(self, user_id):
        now = datetime.datetime.now()
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
                "last": "",
                "wins": 0
            }
            log(f'[Fishing] - {self.message.author} has no fishing profile, creating...')
            self.write_json(f"{self.profile_dir}{user_id}.json", data)
            return data, f"{self.profile_dir}{user_id}.json"

    def handle_profile(self):
        if self.user_profile["xp"] + self.caught_fish["xp_worth"] >= self.user_profile["xpCap"]:
            diffrence = (self.user_profile["xp"] + self.caught_fish["xp_worth"]) - self.user_profile["xpCap"]
            self.user_profile["level"] += 1
            self.user_profile["xp"] = diffrence
            self.user_profile["xpCap"] += (10 + self.user_profile["level"])
            self.isDing = self.user_profile["level"]
        else:
            self.user_profile["xp"] += self.caught_fish["xp_worth"]
            self.isDing = 0

    def handle_money(self, money):
        # print(f'Giving {self.user_name} {money} money')
        self.user_profile["money"] += money

    def fishoff_handler(self):
        now = datetime.datetime.now()
        user_id_str = str(self.user_id)
        if not os.path.isfile(f"./local/fishing/fishoff.json"):
            data = {
                user_id_str:
                    {
                        "name": self.caught_fish["name"],
                        "weight": self.caught_fish["weight"],
                        "unique": self.caught_fish["unique"],
                        "shiny": self.isShiny,
                        "time": str(now.isoformat())
                    }
            }
            current_largest_fish = self.caught_fish["weight"]
            self.write_json(f"./local/fishing/fishoff.json", data)

        else:
            with open(f"./local/fishing/fishoff.json", "r") as f:
                data = json.load(f)
            weights = [info['weight'] for info in data.values() if 'weight' in info]
            current_largest_fish = max(weights, default=0)

            if user_id_str not in data:
                data[user_id_str] = {}
                data[user_id_str]["name"] = self.caught_fish["name"]
                data[user_id_str]["weight"] = self.caught_fish["weight"]
                data[user_id_str]["unique"] = self.caught_fish["unique"]
                data[user_id_str]["shiny"] = self.isShiny
                data[user_id_str]["time"] = str(now.isoformat())

                self.write_json(f"./local/fishing/fishoff.json", data)

            else:
                if self.caught_fish["weight"] > data[user_id_str]["weight"]:
                    data[user_id_str]["name"] = self.caught_fish["name"]
                    data[user_id_str]["weight"] = self.caught_fish["weight"]
                    data[user_id_str]["unique"] = self.caught_fish["unique"]
                    data[user_id_str]["shiny"] = self.isShiny
                    data[user_id_str]["time"] = str(now.isoformat())

                    self.write_json(f"./local/fishing/fishoff.json", data)

        if self.caught_fish["weight"] > current_largest_fish:
            return True
        else:
            return False

    def handle_bucket(self):
        self.user_bucket = None
        now = datetime.datetime.now()
        # if the bucket does not exist create and add fish
        if not os.path.isfile(f"{self.bucket_dir}{self.user_id}.json"):
            data = {
                self.caught_fish["name"]:
                    {
                        "weight": self.caught_fish["weight"],
                        "worth": self.caught_fish["value"],
                        "unique": self.caught_fish["unique"],
                        "shiny": self.isShiny,
                        "time": str(now.isoformat())
                    }
            }
            self.user_bucket = data
            self.write_json(f"{self.bucket_dir}{self.user_id}.json", data)

            return None, 0.0
        else:
            # add fish to existing bucket
            with open(f"{self.bucket_dir}{self.user_id}.json", "r") as f:
                data = json.load(f)
            self.user_bucket = data

            if self.caught_fish["name"] in data:  # if user already has the fish
                old_pb = data[self.caught_fish["name"]]["weight"]
                if self.caught_fish["weight"] > data[self.caught_fish["name"]]["weight"]:  # if the dupe is larger
                    data[self.caught_fish["name"]]["weight"] = self.caught_fish["weight"]
                    data[self.caught_fish["name"]]["worth"] = self.caught_fish["value"]
                    data[self.caught_fish["name"]]["unique"] = self.caught_fish["unique"]
                    data[self.caught_fish["name"]]["shiny"] = self.isShiny
                    data[self.caught_fish["name"]]["time"] = str(now.isoformat())

                    self.write_json(f"{self.bucket_dir}{self.user_id}.json", data)

                    return self.user_bucket[self.caught_fish["name"]][
                        "worth"], old_pb  # return the value of the old fish for selling, and pb

                return self.caught_fish["worth"], old_pb  # return value of the new fish for selling, and pb

            data[self.caught_fish["name"]] = {}
            data[self.caught_fish["name"]]["weight"] = self.caught_fish["weight"]
            data[self.caught_fish["name"]]["worth"] = self.caught_fish["value"]
            data[self.caught_fish["name"]]["unique"] = self.caught_fish["unique"]
            data[self.caught_fish["name"]]["shiny"] = self.isShiny
            data[self.caught_fish["name"]]["time"] = str(now.isoformat())

            self.write_json(f"{self.bucket_dir}{self.user_id}.json", data)

            return None, 0.0

    def wr_check(self):
        # if theres no wr file create it
        if not os.path.isfile(f"./local/fishing/wr.json"):
            wrs = {}
            self.write_json("./local/fishing/wr.json", wrs)
        # open wr file
        with open(f"./local/fishing/wr.json", "r") as f:
            wr_data = json.load(f)
        if self.caught_fish["name"] in wr_data:
            old_wr = wr_data[self.caught_fish["name"]]["weight"]
            old_wr_holder = wr_data[self.caught_fish["name"]]["holder"]
            # if wr fish
            if self.caught_fish["weight"] > wr_data[self.caught_fish["name"]]["weight"]:
                wr_data[self.caught_fish["name"]]["weight"] = self.caught_fish["weight"]
                wr_data[self.caught_fish["name"]]["holder"] = self.user_name
                wr_data[self.caught_fish["name"]]["time"] = str(datetime.datetime.now().isoformat())
                self.write_json("./local/fishing/wr.json", wr_data)

            return old_wr, old_wr_holder
        else:
            # fish is not on wr file
            wr_data[self.caught_fish["name"]] = {}
            wr_data[self.caught_fish["name"]]["weight"] = self.caught_fish["weight"]
            wr_data[self.caught_fish["name"]]["holder"] = self.user_name
            wr_data[self.caught_fish["name"]]["time"] = str(datetime.datetime.now().isoformat())
            self.write_json("./local/fishing/wr.json", wr_data)

            return 0.0, ""

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
        return sizes[x], x

    # this is directly copied from 1.0 for now
    # should probably redo this to read directly from the caught fish dict instead of feeding a thousand paramaters
    def fishing_embed(self, username, fish, joke, fish_class, weight, value, xp, shiny, unique, weight_c, ding, leading,
                      old_pb=0.0, old_wr=0.0, dethroned=""):

        embed = Embed()
        embed.title = f"{username} caught a {weight_c} {fish}!"
        embed.description = f"*{joke}*\n**class {fish_class}**"
        embed.colour = 0x99ff
        # embed.add_field(name="Class", value=f"**{fish_class}**", inline=True)
        embed.add_field(name="Weight", value=f"**{weight}**", inline=True)
        embed.add_field(name="Xp", value=f"**{xp}**", inline=True)
        embed.add_field(name="Bells", value=f"**{value}**", inline=True)
        if old_pb == 0.0:
            embed.add_field(name="New fish type!", value="Great addition to your bucket!")
        elif weight > old_pb:
            embed.add_field(name="NEW RECORD! Selling old...", value=f"*Your previous one was only {old_pb} lbs*")
        else:
            embed.add_field(name=f"Selling {fish}...", value=f"You already have one at {old_pb} lbs!")
        if old_wr == 0.0 and dethroned == "":
            embed.add_field(name="NEW WORLD RECORD!", value=f"*You caught the first {fish}!*")
        elif self.caught_fish["weight"] > old_wr and dethroned != "":
            embed.add_field(name="NEW WORLD RECORD!", value=f"*Previous record was {old_wr} lbs by {dethroned}*")
        if leading:
            embed.add_field(name="FISHOFF LEADER!", value=f"This fish now leads the competition")
        if shiny:
            embed.add_field(name="!", value=f"SHINY!")
        if unique:
            embed.add_field(name="!", value=f"UNIQUE!")
        if ding != 0:
            embed.add_field(name="DING!", value=f"{username} is now level {ding}!")
        fishwithoutspaces = fish.replace(" ", "")
        icon_url = f"http://thedarkzone.se:8080/fishicons/{fishwithoutspaces}.png"
        embed.set_thumbnail(url=icon_url)
        return embed

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        # if debug_on():
        #    log(f'[Fishing] - Wrote {filepath}')

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]
