# command to input and save time objects to string to use with reminders
# a string like this need regex magic NotLikeThis
# remindme 10weeks 20days 2hours 5minutes 10seconds "Birthday boy"
# if date do the other thing

import os
import json
import datetime
import re

from systems.logger import log, debug_on

class Remindme:
    def __init__(self):
        self.reminder_path = './local/reminders.json'

    async def command(self, message):
        # make json if none excists
        if not os.path.exists(self.reminder_path):
            # make json if none excists
            main_dict = {"reminders": {}}
            self.write_json(self.reminder_path, main_dict)


        with open(self.reminder_path, "r") as f:
            data = json.load(f)

        reminder_dict = {}
        user_id_str = str(message.author.id)
        content = message.content
        user_msg = "test reminder woodhouses birthday" # this needs parsing from regex the message they want to recive with the reminder.

        when = self.get_time()
        data["reminders"][when] = {}
        data['reminders'][when]["id"] = user_id_str
        data['reminders'][when]["msg"] = user_msg
        self.write_json(self.reminder_path, data)

        await message.add_reaction("👍")

    def get_time(self):
        # get time right now
        now = datetime.datetime.now()
        # get time user wants to be reminded of
        then = datetime.timedelta(hours=4)  # these parameters need to be parsed in with REeeeeee
        # make requested timedate into an isostring
        when = (now + then).isoformat()
        # use x = datetime.datetime.fromisoformat(when) when getting the string back to a timedate object in the task
        return when

    def get_date(self):
        pass

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)


