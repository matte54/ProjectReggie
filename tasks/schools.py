import asyncio
import datetime
import random

from systems.logger import log
from systems.varmanager import VarManager

SCHOOL_CHANCE = 35  # %


class Schools:
    def __init__(self, client):
        self.client = client
        self.varmanager = VarManager()
        self.fishing_channels = None
        self.school_active = False
        self.school_length = random.randint(15, 60)
        self.school_types = ["class2", "class3", "class4", "class5", "class6", "class7", "trip"]
        # create the variable if needed
        if not self.varmanager.read("school"):
            firsttimedate = datetime.datetime.now() - datetime.timedelta(hours=24)
            self.varmanager.write("school", (False, None, firsttimedate.isoformat()))

    async def main_loop(self):
        await asyncio.sleep(10)
        if self.varmanager.read("school")[0]:  # do this check here to survive thru restarts?
            self.school_active = True
        self.fishing_channels = self.collect_channel_ids()

        while True:
            # check how long its been since last school
            time_difference = datetime.datetime.now() - datetime.datetime.fromisoformat(
                self.varmanager.read("school")[2])
            if time_difference >= datetime.timedelta(hours=24) and not self.school_active:
                if random.randint(1, 100) < SCHOOL_CHANCE:
                    school_name = random.choice(self.school_types)
                    school_start = datetime.datetime.now()
                    self.varmanager.write("school", (True, school_name, school_start.isoformat()))
                    log(f'[Schools] - {school_name} school appeared and is staying for {self.school_length}m')
                    self.school_active = True
                    # send message to all fishing channels
                    for channel in self.fishing_channels:
                        ch = self.client.get_channel(channel)
                        if school_name == "trip":
                            await ch.send(f'```yaml\n\na mindboggling random school appeared look at the colors!```')
                        else:
                            await ch.send(f'```yaml\n\na {school_name} school just appeared in the waters nearby!```')
                        await asyncio.sleep(2)
                else:
                    log(f'[Schools] - Possible but sleepin')
                    await asyncio.sleep(3600)
            else:
                if self.school_active:
                    other_time_difference = datetime.datetime.now() - datetime.datetime.fromisoformat(
                        self.varmanager.read("school")[2])
                    if other_time_difference >= datetime.timedelta(minutes=self.school_length):
                        oldvariable = self.varmanager.read("school")
                        oldvariable[0] = False
                        oldvariable[1] = None
                        self.varmanager.write("school", oldvariable)
                        self.school_active = False
                        log(f'[Schools] - The school left')
                        for channel in self.fishing_channels:
                            ch = self.client.get_channel(channel)
                            await ch.send(f'```yaml\n\nThe school has left the area```')
                            await asyncio.sleep(2)
                    else:
                        if random.randint(1, 100) < 25:
                            log(f'[Schools] - Waiting for the school to end')
                        await asyncio.sleep(60)
                else:
                    log(f'[Schools] - Schools sleepin')
                    await asyncio.sleep(3600)

    def collect_channel_ids(self):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            return fishing_channels
