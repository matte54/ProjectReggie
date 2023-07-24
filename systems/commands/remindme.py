# command to input and save time objects to string to use with reminders
# remindme 10weeks 20days 2hours 5minutes 10seconds "Birthday boy"
# if date do the other thing?

import os
import json
import datetime
import re

from systems.logger import log, debug_on


class Remindme:
    def __init__(self):
        self.reminder_path = './local/reminders.json'
        self.re_pattern = r'remindme(?:(?:\s+(\d+)weeks?)|)(?:(?:\s+(\d+)days?)|)(?:(?:\s+(\d+)hours?)|)(?:(?:\s+(\d+)minutes?)|)(?:(?:\s+(\d+)seconds?)|)\s+"([^"]+)"'
        self.error_help = f'Invalid reminder syntax, try "$remindme 2weeks 3days 30hours 5minutes "Woodhouses birthday" (only 1 time increment is required)'

    async def command(self, message):
        # make json if none excists
        if not os.path.exists(self.reminder_path):
            # make json if none excists
            main_dict = {"reminders": {}}
            self.write_json(self.reminder_path, main_dict)

        with open(self.reminder_path, "r") as f:
            data = json.load(f)

        user_id_str = str(message.author.id)
        content = message.content.replace('$', '')
        parsed_reminder = self.parse_msg(content)
        # if reminder is entered wrong send msg to show how
        if parsed_reminder is None:
            await message.channel.send(self.error_help)
            return
        when = self.get_time(parsed_reminder)

        data["reminders"][when] = {}
        data['reminders'][when]["id"] = user_id_str
        data['reminders'][when]["msg"] = parsed_reminder["message"]
        self.write_json(self.reminder_path, data)

        if debug_on():
            log(f'[Remindme] - Added reminder for user {message.author}!')
        await message.add_reaction("👍")

    def parse_msg(self, msg_string):
        match = re.match(self.re_pattern, msg_string)

        try:
            if match:
                weeks, days, hours, minutes, seconds, message = match.groups()

                time_units = {
                    "weeks": int(weeks) if weeks else 0,
                    "days": int(days) if days else 0,
                    "hours": int(hours) if hours else 0,
                    "minutes": int(minutes) if minutes else 0,
                    "seconds": int(seconds) if seconds else 0,
                }

                # if no time is specified return None
                total_time_units = sum(time_units.values())
                if total_time_units == 0:
                    return None

                return {key: value for key, value in time_units.items() if value} | {"message": message}
            else:
                return None
        except ValueError:
            return None

    def get_time(self, parsed_reminder):
        # Dictionary to store time values and their corresponding keys
        time_units = {
            "weeks": 0,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0
        }

        for key, value in parsed_reminder.items():
            if key in time_units:
                time_units[key] = value

        weeks = time_units["weeks"]
        days = time_units["days"]
        hours = time_units["hours"]
        minutes = time_units["minutes"]
        seconds = time_units["seconds"]

        then = datetime.timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        # get time right now
        now = datetime.datetime.now()
        # make requested timedate into an isostring
        when = (now + then).isoformat()
        # use x = datetime.datetime.fromisoformat(when) when getting the string back to a timedate object in the task
        return when

    def get_date(self):
        pass

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
