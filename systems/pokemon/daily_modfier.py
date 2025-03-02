import os
import json
import random

from systems.logger import log


class DailyModifier:
    current_modifier = None

    def __init__(self):
        self.modifiers_default_list = ["default", "battles", "xp", "pulls", "money", "chansey", "battles"]
        self.modifiers_file = './local/pokemon/modifiers.json'
        self.modifiers_data = None

    def startup_modifier(self):
        if not os.path.exists(self.modifiers_file):
            # file does not exist create
            self.create_file()
        # load datafile
        self._load_json()

        if all(self.modifiers_data.values()):
            # check if all modifiers has been used then recreate the default file and reload
            log(f'[Pokemon][Daily mod] - all modifiers has been used, reseting...')
            self.create_file()
            self._load_json()

        # find all keys that are False (ie not used yet)
        valid_keys = [key for key, value in self.modifiers_data.items() if not value]
        chosen_modifer = random.choice(valid_keys)

        # set chosen modifier to True to indicate its been used
        self.modifiers_data[chosen_modifer] = True
        self._write_json(self.modifiers_file, self.modifiers_data)

        log(f'[Pokemon][Daily mod] - using modifier {chosen_modifer}')

        DailyModifier.current_modifier = chosen_modifer
        return chosen_modifer

    def create_file(self):
        data = {key: False for key in self.modifiers_default_list}
        self._write_json(self.modifiers_file, data)

    def _write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)

    def _load_json(self):
        try:
            with open(self.modifiers_file, "r", encoding='UTF-8') as f:
                self.modifiers_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.create_file()  # Recreate the file if it fails
            self._load_json()

    def read_modifier(self):
        return DailyModifier.current_modifier
