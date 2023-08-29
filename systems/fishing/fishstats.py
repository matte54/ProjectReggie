import json
import os


class Fishstat:
    def __init__(self):
        self.statfile_path = "./local/fishing/stats.json"

        # create stat file if none
        if not os.path.exists(self.statfile_path):
            blank_dict = {"alltime": {"fails": 0, "catches": 0, "shinies": 0, "uniques": 0},
                          "month": {"fails": 0, "catches": 0, "shinies": 0, "uniques": 0},
                          "fish": {},
                          "users": {}
                          }
            self.write_json(self.statfile_path, blank_dict)

    def stat_this(self, user_id, fish_data, fail, shiny):
        user_id_str = str(user_id)
        with open(self.statfile_path, "r") as f:
            stat_data = json.load(f)
        # create the user dictionary if needed
        if user_id_str not in stat_data["users"]:
            user_dict = {"fails": 0, "catches": 0, "shinies": 0, "uniques": 0}
            stat_data["users"][user_id_str] = user_dict

        # add fail data
        if fail:
            stat_data["alltime"]["fails"] += 1
            stat_data["month"]["fails"] += 1
            stat_data["users"][user_id_str]["fails"] += 1

        # add catch data
        if fish_data:
            # create the fish data if we havent seen it b4
            if fish_data["name"] not in stat_data["fish"]:
                fish_dict = {"catches": 0, "shinies": 0}
                stat_data["fish"][fish_data["name"]] = fish_dict

            stat_data["alltime"]["catches"] += 1
            stat_data["month"]["catches"] += 1
            stat_data["fish"][fish_data["name"]]["catches"] += 1
            stat_data["users"][user_id_str]["catches"] += 1

            # add conditional fish data if needed
            # shinies
            if shiny:
                stat_data["users"][user_id_str]["shinies"] += 1
                stat_data["fish"][fish_data["name"]]["shinies"] += 1
                stat_data["alltime"]["shinies"] += 1
                stat_data["month"]["shinies"] += 1

            # uniques
            if fish_data["unique"]:
                stat_data["users"][user_id_str]["uniques"] += 1
                stat_data["alltime"]["uniques"] += 1
                stat_data["month"]["uniques"] += 1

        self.write_json(self.statfile_path, stat_data)

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
