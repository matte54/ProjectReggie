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

    def get_profile(self, message):
        self.userid = message.author.id
        self.username = self.get_user_name(message.author.id)
        now = datetime.datetime.now()
        # if profile exists load and return
        if os.path.isfile(f"{self.profiles_path}{self.userid}.json"):
            with open(f"{self.profiles_path}{self.userid}.json", "r") as f:
                data = json.load(f)
            return data, f"{self.profiles_path}{self.userid}.json"
        # if it does not, create AND return
        else:
            data = {}
            blank_profile_dict = {
                "money": 0.0,
                "cards": 0,
                "last": "",
                "boosters_opened": 0,
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
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
