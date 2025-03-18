import json
import asyncio
import os
import glob
import discord

from systems.logger import log
from systems.varmanager import VarManager


class AchivementTracker:
    def __init__(self, client):
        self.client = client
        self.varmanager = VarManager()
        self.run = True

        self.pokemon_channels = None

        self.MILESTONE_LOG_FILE = "./local/pokemon/milestone_log.json"
        self.profile_path = './local/pokemon/profiles/'

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

    async def scan_profile_data(self):
        json_files = glob.glob(os.path.join(self.profile_path, "*.json"))
        for file in json_files:
            await self.process_profile(file)

    async def process_profile(self, file):
        with open(file, "r", encoding='UTF-8') as f:
            profile_data = json.load(f)

        username = profile_data["profile"]["username"]
        #log(f'[Pokemon][Achievements][DEBUG] - Parsing {username}\'s profile')

        milestones = [10, 50, 100, 250, 500, 1000,
                      1500, 2000, 3000, 4000, 5000,
                      6000, 7500, 9000, 11000, 13000,
                      15000, 17500, 20000]

        keys = ["cards", "boosters_opened", "battles_won", "battles_lost", "chansey_picks", "upgrades"]

        milestone_log = self.load_milestone_log()
        user_log = milestone_log.get(username)

        # If first time seeing this user, set their baseline
        if user_log is None:
            log(f'[Pokemon][Achievements][DEBUG] - First time tracking {username}, setting baseline.')

            # Set current achievements as "already reached"
            user_log = {}
            for key in keys:
                value = profile_data["profile"].get(key, 0)
                user_log[key] = [m for m in milestones if m <= value]  # Store milestones already reached

            milestone_log[username] = user_log
            self.save_milestone_log(milestone_log)
            return  # Exit to avoid logging past achievements

        # Now process new milestones
        for key in keys:
            value = profile_data["profile"].get(key, 0)
            logged_milestones = set(user_log.get(key, []))

            # Find new milestones that were not logged before
            new_milestones = [m for m in milestones if m <= value and m not in logged_milestones]

            if new_milestones:
                latest_milestone = max(new_milestones)  # Highest newly reached milestone
                log(f'[Pokemon][Achievements] - [{username}] {value} {key} (New Milestone: {latest_milestone})')

                # Update milestone log
                await self.send_toast(username, key, latest_milestone)
                logged_milestones.update(new_milestones)
                user_log[key] = list(logged_milestones)

        # Save updated milestone log
        milestone_log[username] = user_log
        self.save_milestone_log(milestone_log)

    async def check_set_milestones(self):
        pass

    async def send_toast(self, username, stat, value):
        stat = stat.replace("_", " ")
        toast = f"""```yaml\n\n🎉 **{username} reached a new milestone {value} {stat}!** 🎉```"""
        await self.send_to_all(toast)

    async def main(self):
        await self.collect_channel_ids()

        await asyncio.sleep(10)
        log(f'[Pokemon][Achivements] - Initilizing')

        while self.run:
            await asyncio.sleep(60)
            await self.scan_profile_data()

    def load_milestone_log(self):
        if os.path.exists(self.MILESTONE_LOG_FILE):
            with open(self.MILESTONE_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_milestone_log(self, log_data):
        with open(self.MILESTONE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4)

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
