# --- profile , card database, and money handler in here ---

from systems.logger import debug_on, log

import datetime
import json, os

from systems.pokemon.set_data import x as set_data


class Pokehandler:
    def __init__(self, client):
        # define paths
        self.profiles_path = "./local/pokemon/profiles/"
        self.setdata_path = "./data/pokemon/setdata/"

        self.setdatalist = set_data

        self.userid = None
        self.username = None
        self.current_profile = None

    def get_profile(self, message, chansey=None):
        if chansey:
            self.userid = chansey
            self.username = self.get_user_name(chansey)
        else:
            self.userid = message.author.id
            self.username = self.get_user_name(message.author.id)
        now = datetime.datetime.now()
        # if profile exists load and return
        if os.path.isfile(f"{self.profiles_path}{self.userid}.json"):
            with open(f"{self.profiles_path}{self.userid}.json", "r") as f:
                data = json.load(f)
            # check for missing entries here
            self.check_missing_keys(data)

            return data, f"{self.profiles_path}{self.userid}.json"
        # if it does not, create AND return
        else:
            data = {}
            blank_profile_dict = {
                "username": self.username,
                "money": 0.0,
                "cards": 0,
                "last": "",
                "price": False,
                "boosters_opened": 0,
                "battles_won": 0,
                "battles_lost": 0,
                "chansey_picks": 0,
                "level": 1,
                "xp": 0,
                "xp_cap": 20,
            }
            data["profile"] = blank_profile_dict
            data["sets"] = {}
            for set_item in self.setdatalist:
                data["sets"][set_item[0]] = {}

            log(f'[Pokemon] - {self.username} has no Pokemon profile, creating...')
            self.write_json(f"{self.profiles_path}{self.userid}.json", data)
            return data, f"{self.profiles_path}{self.userid}.json"

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    def write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)

    def check_missing_keys(self, data):
        required_keys = [
             "username",
             "money",
             "cards",
             "last",
             "price",
             "boosters_opened",
             "battles_won",
             "battles_lost",
             "chansey_picks",
             "level",
             "xp",
             "xp_cap",
             "battle_upgrade",
             "money_cap",
             "upgrades",
             ]
        default_values = {
            "username": self.username,
            "money": 0.0,
            "cards": 0,
            "last": "",
            "price": False,
            "boosters_opened": 0,
            "battles_won": 0,
            "battles_lost": 0,
            "chansey_picks": 0,
            "level": 1,
            "xp": 0,
            "xp_cap": 20,
            "upgrades": 0,
            "battle_upgrade": 0,
            "money_cap": 10000,
        }

        # Find missing keys
        missing_keys = [key for key in required_keys if key not in data["profile"]]

        if missing_keys:  # Only proceed if there are missing keys
            for key in missing_keys:
                data["profile"][key] = default_values.get(key, None)

            log(f'[Pokemon] - {self.username} has missing profile keys... adding {missing_keys}')
            self.write_json(f"{self.profiles_path}{self.userid}.json", data)


