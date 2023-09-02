import json
import asyncio
import os
import datetime

from systems.logger import log


class Event_handler:
    def __init__(self, client):
        self.client = client
        self.path = "./local/events.json"
        self.last_timestamp = None
        self.events_dict = None

    def has_file_changed(self):
        current_timestamp = os.path.getmtime(self.path)
        return current_timestamp != self.last_timestamp

    def write_json(self):
        with open(self.path, "w") as f:
            json.dump(self.events_dict, f, indent=4)

    async def track_events(self):
        await asyncio.sleep(10)
        if os.path.exists(self.path):
            self.last_timestamp = os.path.getmtime(self.path)
            with open(self.path, "r") as f:
                self.events_dict = json.load(f)
        else:
            log(f'[Event Handler] - No events file found, handler is off')
            return

        while True:
            if self.has_file_changed():  # if the file has been updated since last loop, reload it.
                with open(self.path, "r") as f:
                    self.events_dict = json.load(f)
                self.last_timestamp = os.path.getmtime(self.path)

            temp_list = []
            for key in self.events_dict:
                event_date = datetime.date.fromisoformat(self.events_dict[key]["date"])
                if event_date == datetime.date.today():
                    log(f'[Event Handler] - Event id {key} is today.')
                    channel = self.client.get_channel(self.events_dict[key]["channel"])
                    await channel.send(f'```yaml\n\n* EVENT TODAY *\n {self.events_dict[key]["msg"]}```')
                    temp_list.append(key)
                if event_date < datetime.date.today():
                    # somehow this date has passed and is still in here, delete
                    log(f'[Event Handler] - Error: Event id {key} is in the database but has passed, deleting.')
                    temp_list.append(key)

            if temp_list:  # do changes here cause you cant do stuff while looping
                for i in temp_list:
                    del self.events_dict[i]
                self.write_json()
            await asyncio.sleep(300)  # this should be alot longer on live maybe 10 minutes
