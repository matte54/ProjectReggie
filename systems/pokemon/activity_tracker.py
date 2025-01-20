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
        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        with open(self.activity_file, "r", encoding='UTF-8') as f:
            data = json.load(f)

        active_users_yesterday = []
        for userid, activity_time in data.items():
            activity_datetime = datetime.fromisoformat(activity_time)

            # Check if the activity time is within yesterday's range
            if yesterday_start <= activity_datetime <= yesterday_end:
                active_users_yesterday.append(userid)

        log(f"[Pokemon] - {active_users_yesterday}")

    def startup(self):
        log(f"[Pokemon] - Init activity")

    def write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)
