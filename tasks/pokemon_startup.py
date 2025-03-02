import json
import asyncio
import os
import discord
from datetime import datetime

from systems.logger import log
from systems.varmanager import VarManager
from systems.pokemon import activity_tracker
from systems.pokemon import daily_modfier


TARGETHOUR = 00
BASEREWARD = 100


class PokemonStartup:
    def __init__(self, client):
        self.client = client
        self.varmanager = VarManager()
        self.activitytracker = activity_tracker.Tracker()

        self.run = True
        self.current_hour = None
        self.rewarded = False
        self.pokemon_channels = None
        self.modifier = daily_modfier.DailyModifier()

        self.profiles_path = './local/pokemon/profiles/'

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

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

    def write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    async def rewards(self):
        mod_string = await self.describe_modifier()
        rewardstring = f"```yaml\n\n"
        rewardstring += f"Welcome to a new day of Pokémon!\n"
        if mod_string:
            rewardstring += f'Today has a modifier: {mod_string}!\n'
        rewardstring += f'** Daily activity rewards **\nrewards for active players (level based)\n'
        id_list = self.activitytracker.read_activity()
        log(f'[Pokemon][Rewards] - Giving out activity rewards to {id_list}')
        for userid in id_list:
            name = self.get_user_name(userid)
            with open(f'{self.profiles_path}{userid}.json', "r", encoding='UTF-8') as f:
                profile_data = json.load(f)
            level = profile_data["profile"]["level"]
            reward = (BASEREWARD * level) / 5
            profile_data["profile"]["money"] += reward

            self.write_json(f'{self.profiles_path}{userid}.json', profile_data)

            rewardstring += f'{name} + ${reward}\n'
        rewardstring += f'```'

        return rewardstring

    async def describe_modifier(self):
        i = self.modifier.read_modifier()
        if i == "default":
            return ""
        if i == "battles":
            return "battle limit X2"
        if i == "xp":
            return "XP X2"
        if i == "pulls":
            return "Free pull ½ CD"
        if i == "money":
            return "Money X2"
        if i == "chansey":
            return "Chansey picks X2"

    async def main(self):
        await self.collect_channel_ids()
        await asyncio.sleep(10)
        log(f'[Pokemon][Rewards]- Initilizing')
        while self.run:
            now = datetime.now()
            if now.hour == TARGETHOUR and not self.rewarded:
                self.current_hour = int(now.hour)
                self.rewarded = True

                msg = await self.rewards()
                await self.send_to_all(msg)

            await asyncio.sleep(60)

