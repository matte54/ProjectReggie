import json
import os
from datetime import datetime, timedelta

from systems.logger import debug_on, log


class Tracker:
    def __init__(self):
        self.activity_file = "./local/pokemon/activity.json"

        if not os.path.exists(self.activity_file):
            log(f"[Pokemon] - Creating activity file")
            self.write_json(self.activity_file, {})

    def add_activity(self, userid, now):
        with open(self.activity_file, "r", encoding='UTF-8') as f:
            data = json.load(f)

        userid = str(userid)
        data[userid] = now

        self.write_json(self.activity_file, data)

    def read_activity(self):
        # Calculate the timestamp for 24 hours ago
        last_24_hours = datetime.now() - timedelta(hours=24)

        with open(self.activity_file, "r", encoding='UTF-8') as f:
            data = json.load(f)

        active_users_last_24_hours = []
        for userid, activity_time in data.items():
            activity_datetime = datetime.fromisoformat(activity_time)

            # Check if the activity time is within the last 24 hours
            if activity_datetime >= last_24_hours:
                active_users_last_24_hours.append(userid)

        log(f"[Pokemon][DEBUG] - activity IDS {active_users_last_24_hours}")
        return active_users_last_24_hours

    def startup(self):
        # just here to create the object at startup for init to run
        #log(f"[Pokemon] - Init activity")
        pass

    def write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)
