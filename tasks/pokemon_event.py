import asyncio
import discord
import random
import os
import json
from datetime import datetime

from systems.logger import log
from systems.varmanager import VarManager
from systems.commands import cmd_tcg
from systems.pokemon import event
from systems.pokemon import pokehandler
from systems.pokemon.event_names import prefixes, suffixes

DEBUG = True


class Pokemoneventhandler:
    def __init__(self, client):
        self.client = client
        self.tcg = cmd_tcg.Tcg
        self.varmanager = VarManager()
        self.pokehandler = pokehandler.Pokehandler(self.client)
        self.event = event.Eventmanager()

        self.setdata_path = './data/pokemon/setdata/'
        self.pokemon_channels = []
        self.last_friday_run = None
        self.last_saturday_run = None
        self.eventname = ""

    async def friday_task(self):
        if self.eventname:
            return
        event_set = await self.pick_event_set()

        event_data = await self.event.start_event(event_set)

        # name event and store
        self.eventname = f'{random.choice(prefixes)} {event_data["name"]} {random.choice(suffixes)}'
        self.varmanager.write("pokemon_event_name", self.eventname)
        log(f'[Pokemon][Event Handler] - Starting event "{self.eventname}"')

        # clear battle que and daily list
        self.tcg.battlelist = []
        self.tcg.battletracker = {}
        log(f'[Pokemon][Event Handler] - clearing battle que/list')

        # reset free pulls
        user_profiles_list = await self.tcg.find_json_files(self, './local/pokemon/profiles/')
        for profile in user_profiles_list:
            with open(profile, "r") as f:
                profile_data = json.load(f)
            profile_data["profile"]["last"] = ""
            self.pokehandler.write_json(profile, profile_data)
        log(f'[Pokemon][Event Handler] - reseting free pulls')

        event_announcement = f"""```yaml

        🎉 **{self.eventname} ({event_set}) Has Begun!** 🎉

        📂 **Available Cards:** {event_data["total"]}  
        🃏 **Set Exclusive:** All free packs and battles feature only cards from this set!  
        ♟️ **Resets Applied:** Battle queue, daily battle limits, and free pulls have been reset!

        🔥 **Get ready, Trainers!** Test your luck, and collect 'em all!

        💥 Good luck and have fun! 💥
        ```"""

        await self.send_to_all(event_announcement)

    async def saturday_task(self):
        log(f'[Pokemon][Event Handler] - Stopping event')

        event_summary_text = await self.event.stop_event()
        await self.send_to_all(event_summary_text)

        # clear battle que and daily list
        self.tcg.battlelist = []
        self.tcg.battletracker = {}
        log(f'[Pokemon][Event Handler] - clearing battle que/list')

        self.eventname = ""
        self.varmanager.write("pokemon_event_name", "")
        return

    async def main(self):
        await asyncio.sleep(10)
        log(f'[Pokemon][Event Handler] - Initilizing')
        await self.collect_channel_ids()

        while True:
            now = datetime.now()

            # Check for 3 PM on Friday
            if now.weekday() == 4 and now.hour == 15 and self.last_friday_run != now.date():
                await self.friday_task()
                self.last_friday_run = now.date()

            # Check for 8 PM on Saturday
            if now.weekday() == 6 and now.hour == 20 and self.last_saturday_run != now.date():
                await self.saturday_task()
                self.last_saturday_run = now.date()

            """
            if DEBUG:
                # testing trigger
                await self.friday_task()
                await asyncio.sleep(30)
                await self.saturday_task()
            """
            await asyncio.sleep(60)

    async def pick_event_set(self):
        # randomly pick a set with atleast this many cards available
        valid_entries = []
        minimum_cards = 85

        for filename in os.listdir(self.setdata_path):
            if filename.endswith(".json"):
                filepath = os.path.join(self.setdata_path, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        if isinstance(data, dict) and "total" in data and isinstance(data["total"], int):
                            if data["total"] >= minimum_cards:
                                valid_entries.append(data)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    log(f'[Pokemon][Event Handler] - Skipping {filename}: {e}')

        if not valid_entries:
            return None

        log(f'[Pokemon][Event Handler] - {len(valid_entries)} valid sets to pick')
        random_entry = random.choice(valid_entries)
        return random_entry.get("id")

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

    async def send_msg(self, channel_id, msg):
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            ch = self.client.get_channel(channel_id)

            if ch is None:
                log(f'[Pokemon]- Channel {channel_id} not found. Retrying in {delay * (2 ** attempt)}s...')
            else:
                try:
                    x = await ch.send(msg)
                    break  # Successfully sent, exit retry loop
                except (discord.HTTPException, discord.Forbidden, discord.NotFound) as e:
                    log(f'[Pokemon]- Error sending message (attempt {attempt + 1}/{max_retries}): {e}')

            await asyncio.sleep(delay * (2 ** attempt))

        else:  # This else runs only if all retries fail
            log(f'[Pokemon]- Failed to send message to {channel_id} after {max_retries} retries.')

    async def send_to_all(self, msg):
        max_retries = 3
        delay = 2
        messages = []

        for channel_id in self.pokemon_channels:
            for attempt in range(max_retries):
                ch = self.client.get_channel(channel_id)

                if ch is None:
                    log(f'[Pokemon]- Channel {channel_id} not found. Retrying in {delay * (2 ** attempt)}s...')
                else:
                    try:
                        x = await ch.send(msg)
                        messages.append(x)
                        break  # Successfully sent, exit retry loop
                    except (discord.HTTPException, discord.Forbidden, discord.NotFound) as e:
                        log(f'[Pokemon]- Error sending message (attempt {attempt + 1}/{max_retries}): {e}')

                await asyncio.sleep(delay * (2 ** attempt))

            else:  # This else runs only if all retries fail
                log(f'[Pokemon]- Failed to send message to {channel_id} after {max_retries} retries.')

        return messages
