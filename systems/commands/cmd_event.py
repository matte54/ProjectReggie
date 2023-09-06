import os
import json
import datetime
import re
import string
import random

from systems.logger import log, debug_on


class Event:
    def __init__(self):
        self.msg = None
        self.events_path = './local/events.json'
        self.pattern = r'\d{4}-\d{2}-\d{2}'

        # event vars
        self.event_id = None
        self.event_date = None
        self.event_msg = None
        self.event_channel = None
        self.events_dict = None
        # make sure file exists
        self.create_file()



    async def command(self, message):
        with open(self.events_path, "r") as f:
            self.events_dict = json.load(f)
        self.msg = message.content.replace('$event ', '')
        if self.msg == "up":
            log(f'[Event] - {message.author} is listing upcoming events')
            sorted_entries = sorted(self.events_dict.items(), key=lambda item: item[1]['date'])
            event_str = "-- Upcoming events --\n"
            for item, sorted_date in sorted_entries:
                if sorted_date["channel"] == message.channel.id:
                    event_str += f'{sorted_date["date"]}: {sorted_date["msg"]}\n'
            await message.channel.send(f'```yaml\n\n{event_str}```')
            return
        log(f'[Event] - {message.author} is creating {self.msg}')
        dates = re.findall(self.pattern, self.msg)
        if not dates or len(dates) > 1:
            await message.channel.send("Syntax error, date needs to be yyyy-mm-dd")
            return
        try:
            event_date = datetime.date.fromisoformat(dates[0])
        except ValueError:
            await message.channel.send("Syntax error, thats not a valid date")
            return
        current_date = datetime.date.today()
        if event_date <= current_date:
            await message.channel.send("The date has to be a future one")
            return
        self.msg = self.msg.replace(dates[0], "")  # self.msg should now only be the message

        if len(self.msg) < 1 or len(self.msg) > 80:
            await message.channel.send("Syntax error, the event needs a message to display (less then 150 chars)")
            return
        self.event_date = dates[0]
        self.event_msg = self.msg
        self.event_channel = message.channel.id

        self.make_event()
        self.write_json(self.events_path, self.events_dict)

        await message.add_reaction("👍")

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    def create_file(self):
        # make json if none exists
        if not os.path.exists(self.events_path):
            # make json if none excists
            main_dict = {}
            self.write_json(self.events_path, main_dict)

    def make_event(self):
        self.event_id = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(20))
        self.events_dict[self.event_id] = {}
        self.events_dict[self.event_id]["date"] = self.event_date
        self.events_dict[self.event_id]["msg"] = self.event_msg
        self.events_dict[self.event_id]["channel"] = self.event_channel
