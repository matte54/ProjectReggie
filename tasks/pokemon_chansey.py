import asyncio
import discord
import random
import os
import json
from datetime import datetime, timedelta

from systems.logger import log
from systems.varmanager import VarManager
from systems.pokemon import pokehandler
from systems.pokemon import daily_modfier

from systems.pokemon.rarity_data import x


class Chanseypick:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Chanseypick, cls).__new__(cls)
        return cls._instance

    def __init__(self, client):
        if not hasattr(self, '_initialized'):  # Prevent re-initialization
            self.manual_trigger = asyncio.Event()
            self.client = client
            self.varmanager = VarManager()
            self.pokehandler = pokehandler.Pokehandler(self.client)
            self.modifier = daily_modfier.DailyModifier()

            self.pokemon_channels = []
            self.rarity_data = x
            self.rarity_weights = None
            self.chansey_img = f'./data/pokemon/chansey.png'
            self.chansey_cards = []
            self.chansey_final = None
            self.reaction_time = 600
            self.rare_threshold = 0.3
            self.trigger_times = None

            self._initialized = True  # Mark as initialized

    async def main(self):
        await asyncio.sleep(10)
        log(f'[Pokemon][Chansey] - Initilizing')
        await self.collect_channel_ids()
        self.rarity_weights = {rarity: weight for rarity, weight, blank in self.rarity_data}
        current_mod = self.modifier.read_modifier()
        if current_mod == "chansey":
            self.trigger_times = self.generate_trigger_times(12, 2)
        else:
            self.trigger_times = self.generate_trigger_times()

        while True:
            now = datetime.now()
            if now >= self.trigger_times[0] or self.manual_trigger.is_set():
                if self.manual_trigger.is_set():
                    self.manual_trigger.clear()
                else:
                    self.trigger_times.pop(0)
                    log(f'[Pokemon][Chansey] - Triggering Chansey event! {len(self.trigger_times)} events left today')
                msg_objs = await self.start_chansey()
                users_who_reacted = await self.monitor_reactions(msg_objs)  # Track reactions
                await self.handle_reaction_results(users_who_reacted)  # Handle results after time expires

                # Dynamically wait up to 1 hour
                sleep_task = asyncio.create_task(asyncio.sleep(3600))
                trigger_task = asyncio.create_task(self.manual_trigger.wait())
                done, pending = await asyncio.wait(
                    {sleep_task, trigger_task}, return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel the task that didn't complete
                for task in pending:
                    task.cancel()

            # Dynamically wait up to 10 minutes
            sleep_task = asyncio.create_task(asyncio.sleep(600))
            trigger_task = asyncio.create_task(self.manual_trigger.wait())
            done, pending = await asyncio.wait(
                {sleep_task, trigger_task}, return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel the task that didn't complete
            for task in pending:
                task.cancel()

    async def trigger_event_manually(self):
        # function for manual trigger
        self.manual_trigger.set()
        log(f'[Pokemon][Chansey] - manually starting chansey event')
            
    async def start_chansey(self):
        """Sends the Chansey image to all Pokemon channels and returns message objects."""
        msgs = []
        self.chansey_final = None  # reset chansey cards
        self.chansey_cards = [self.chansey_img]
        self.chansey_final = await self.get_chansey_picks()
        for card in self.chansey_final:
            self.chansey_cards.append(card[1])

        for channel_id in self.pokemon_channels:
            ch = self.client.get_channel(channel_id)
            if ch:
                files = [discord.File(file_path) for file_path in self.chansey_cards]
                msg_object = await ch.send(files=files)
                await msg_object.add_reaction("⭐")  # Pre-add reaction to encourage interaction
                msgs.append(msg_object)

        return msgs

    async def get_chansey_picks(self, base_path="./data/pokemon/sets", num_cards=6):
        common_cards = []
        rare_cards = []

        # Traverse all sets and collect card file paths
        for set_id in os.listdir(base_path):
            set_path = os.path.join(base_path, set_id)
            if os.path.isdir(set_path):
                for card_id in os.listdir(set_path):
                    card_path = os.path.join(set_path, card_id)
                    if card_path.endswith(".json"):
                        with open(card_path, "r", encoding="utf-8") as file:
                            card_data = json.load(file)
                            rarity = card_data.get("rarity", "Common")
                            rarity_weight = self.rarity_weights.get(rarity, 1.0)
                            card_data["rarity_weight"] = rarity_weight

                            if rarity_weight <= self.rare_threshold:
                                rare_cards.append(card_data)
                            else:
                                common_cards.append(card_data)

        # Ensure 4-5 common and 1-2 rare cards
        num_common = random.randint(4, 5)
        num_rare = num_cards - num_common

        # Adjust inverse weighting to favor more common cards more strongly
        selected_common = random.choices(common_cards, weights=[c["rarity_weight"] for c in common_cards],
                                         k=num_common)
        selected_rare = random.choices(rare_cards, weights=[c["rarity_weight"] for c in rare_cards], k=num_rare)

        selected_cards = selected_common + selected_rare
        random.shuffle(selected_cards)  # Shuffle for randomness

        # find card images and put card dict and path to image in a tuple
        final_collection = []
        for card in selected_cards:
            set_id, card_id = card["id"].split("-")
            final_collection.append((card, f'./data/pokemon/images/{set_id}/images/{set_id}-{card_id}.png'))

        return final_collection

    async def handle_reaction_results(self, users):
        if users:
            summary_message = f'```yaml\n\n*** Chansey Pick Summary ***\n'
            for user in users:
                income = 0.0
                new = False

                random.seed(users[user])
                chansey_pick = random.choice(self.chansey_final)
                card_data = chansey_pick[0]
                user_profile_data, user_profile_path = self.pokehandler.get_profile(None, chansey=user)

                user_profile_data["profile"]["chansey_picks"] += 1
                # Ensure the set structure exists
                user_profile_data.setdefault("sets", {}).setdefault(card_data["set"]["id"], {})

                card_id = card_data["id"]
                name = card_data["name"]
                sell_price = card_data["cardmarket"]["prices"]["averageSellPrice"]

                if card_id in user_profile_data["sets"][card_data["set"]["id"]]:
                    # User already owns the card - sell or handle as needed
                    user_profile_data["profile"]["money"] += round(sell_price, 2)
                    if (user_profile_data["profile"]["money"] + round(sell_price, 2)) >= user_profile_data["profile"]["money_cap"]:
                        log(f"[Pokemon] - money over cap")
                    else:
                        income += round(sell_price, 2)
                        log(f"[Pokemon] - {user}s already has '{name}({card_id})' selling.")
                else:
                    # Add card to the user's profile
                    new = True
                    user_profile_data["sets"][card_data["set"]["id"]][card_id] = sell_price
                    user_profile_data["profile"]["cards"] += 1
                self.pokehandler.write_json(user_profile_path, user_profile_data)

                username = self.get_user_name(user)
                summary_message += f"❓ {username} - picked {name} ({card_id}) {'NEW!' if new else 'DUPE!'}{f', sold for {income}' if income else ''}\n"

            summary_message += f'```'
            await self.send_to_all(summary_message)
        else:
            log(f'[Pokemon][Chansey] - No users participated in chansey pick')
            return

    async def monitor_reactions(self, messages) -> list:
        user_reactions = {}  # Store unique userids

        def check(reaction, user) -> bool:
            if user.bot:
                return False  # Ignore bot reactions
            if reaction.message.id not in [msg.id for msg in messages]:
                return False

                # Store reaction with user
            user_reactions[str(user.id)] = hash(reaction.emoji)  # Store as string (Unicode or custom emoji ID)
            return True

        try:
            while True:  # Keep listening until time runs out
                await self.client.wait_for("reaction_add", timeout=self.reaction_time, check=check)

        except asyncio.TimeoutError:
            log(f'[Pokemon][Chansey] - Chansey pick time expired. users that reacted: {user_reactions}')

        # FIX: Delete messages one by one with a small delay to avoid "album" issue
        for msg in messages:
            try:
                await msg.delete(delay=2.0)
            except discord.NotFound:
                log(f'[Pokemon][Chansey] - Message {msg.id} was already deleted.')
            except discord.Forbidden:
                log(f'[Pokemon][Chansey] - No permission to delete message {msg.id}.')
            except discord.HTTPException:
                log(f'[Pokemon][Chansey] - Deleting {msg.id} failed!.')

        return user_reactions  # Return the list of users who reacted

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

    def generate_trigger_times(self, n=6, min_gap_hours=3):
        """Generate n random times within the next 24 hours, with at least min_gap_hours between them."""
        now = datetime.now()
        end_time = now + timedelta(hours=24)  # Limit triggers to within the next 24 hours
        trigger_times = []

        # Start the first trigger at a random time within the next hour
        next_time = now + timedelta(seconds=random.randint(0, 3600))

        for _ in range(n):
            if next_time > end_time:
                break  # Stop if we exceed the 24-hour limit

            trigger_times.append(next_time)

            # Ensure the next trigger is at least `min_gap_hours` later
            next_min_time = next_time + timedelta(hours=min_gap_hours)

            # Pick a random time between next_min_time and end_time, but keep it within bounds
            if next_min_time > end_time:
                break  # Stop if the next trigger would exceed the 24-hour period

            remaining_time = (end_time - next_min_time).total_seconds()
            next_time = next_min_time + timedelta(
                seconds=random.randint(0, int(remaining_time / (n - len(trigger_times) + 1))))

        return sorted(trigger_times)

    async def send_msg(self, channel_id, msg):
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            ch = self.client.get_channel(channel_id)

            if ch is None:
                log(f'[Pokemon] - Channel {channel_id} not found. Retrying in {delay * (2 ** attempt)}s...')
            else:
                try:
                    x = await ch.send(msg)
                    break  # Successfully sent, exit retry loop
                except (discord.HTTPException, discord.Forbidden, discord.NotFound) as e:
                    log(f'[Pokemon] - Error sending message (attempt {attempt + 1}/{max_retries}): {e}')

            await asyncio.sleep(delay * (2 ** attempt))

        else:  # This else runs only if all retries fail
            log(f'[Pokemon] - Failed to send message to {channel_id} after {max_retries} retries.')

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

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]