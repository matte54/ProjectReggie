import json
import datetime
import os

from systems.logger import log

class Banditlife:
    def __init__(self):
        self.profile_template = "./data/banditlife/profile_template.json"
        self.profile_dir = "./local/banditlife/profiles/"

    def create_profile(self, user_id, name_str):
        user_name = self.get_user_name(user_id)
        now = datetime.datetime.now()
        with open(self.profile_template, "r") as f:
            user_profile = json.load(f)

        # set users variables
        user_profile["character"]["name"] = name_str
        user_profile["variables"]["created_at"] = str(now.isoformat())

        self.write_json(f"{self.profile_dir}{str(user_id)}.json", user_profile)
        log(f'[Banditlife] - {user_name} created profile "{name_str}"')

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]