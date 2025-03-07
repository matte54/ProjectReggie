import json
import datetime
import os

from systems.pokemon.set_data import x as set_data
from systems.varmanager import VarManager
from systems.logger import debug_on, log


class Eventmanager:
    def __init__(self):
        self.statfile_path = './local/pokemon/eventstats.json'
        self.varmanager = VarManager()
        self.setdatalist = set_data
        self.set_ids = {t[0] for t in self.setdatalist}

    def _write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    async def start_event(self, set_id):
        if set_id not in self.set_ids:
            return None

        with open(f'./data/pokemon/setdata/{set_id}_setdata.json', "r") as f:
            event_data = json.load(f)

        self.varmanager.write("pokemon_event", set_id)
        await self._create_stat_file(event_data["total"])
        log(f'[Pokemon] - starting event for set {set_id}')
        return event_data

    async def stop_event(self):
        self.varmanager.write("pokemon_event", "")
        log(f'[Pokemon] - stopping event')
        summary = await self.event_summary()
        log(f'[Pokemon] - deleting event stat file')
        os.remove(self.statfile_path)
        return summary

    async def _create_stat_file(self, set_total):
        now = datetime.datetime.now()

        statdata = {}
        common_stats = {
            "event_name": "",
            "event_start": str(now.isoformat()),
            "cards_total": set_total,
            "battles": 0,
            "packs_opened": 0,
            "cards_pulled": 0,
        }
        statdata["common"] = common_stats
        statdata["users"] = {}

        self._write_json(self.statfile_path, statdata)
        log(f'[Pokemon] - creating new stat file for event')

    async def stats(self, userid, cards=None, pack=None, battle_won=None, battle_lost=None):
        userid = str(userid)
        if not os.path.exists(self.statfile_path):
            log(f'[Pokemon] - there is no active event stats file')
            return
        with open(self.statfile_path, "r", encoding="UTF-8") as f:
            statdata = json.load(f)

        # add eventname
        if not statdata["common"]["event_name"]:
            statdata["common"]["event_name"] = self.varmanager.read("pokemon_event_name")
        # create user dict if not existing
        if userid not in statdata["users"]:
            statdata["users"][userid] = {
                "battles_won": 0,
                "battles_lost": 0,
                "packs_opened": 0,
                "cards_pulled": 0,
                "card_list": []
            }
        # handle input
        # cards
        if cards:
            merged_list = statdata["users"][userid]["card_list"] + [item for item in cards if item not in statdata["users"][userid]["card_list"]]
            statdata["users"][userid]["card_list"] = merged_list
            statdata["users"][userid]["cards_pulled"] += len(cards)
            statdata["common"]["cards_pulled"] += len(cards)
        # stats
        if pack:
            statdata["users"][userid]["packs_opened"] += pack
            statdata["common"]["packs_opened"] += pack
        if battle_won:
            statdata["common"]["battles"] += battle_won
            statdata["users"][userid]["battles_won"] += battle_won
        if battle_lost:
            statdata["common"]["battles"] += battle_lost
            statdata["users"][userid]["battles_lost"] += battle_lost

        self._write_json(self.statfile_path, statdata)

    async def handout_rewards(self):
        pass

    async def event_summary(self):
        with open(self.statfile_path, "r", encoding="UTF-8") as f:
            event_data = json.load(f)

        # Parse common event data
        event_name = event_data['common']['event_name']
        start_time = datetime.datetime.fromisoformat(
            event_data['common']['event_start']
        ).strftime("%Y-%m-%d %H:%M:%S")
        total_battles = event_data['common']['battles']
        total_packs = event_data['common']['packs_opened']
        total_cards = event_data['common']['cards_pulled']
        total_available_cards = event_data['common']['cards_total']

        # Build a leaderboard from users sorted by wins (descending), then cards collected
        users = []
        for user_id, stats in event_data['users'].items():
            username = self.get_user_name(user_id)
            cards_collected = stats['cards_pulled']
            collection_percentage = (
                (cards_collected / total_available_cards) * 100
                if total_available_cards > 0 else 0
            )

            users.append({
                "username": username,
                "wins": stats['battles_won'],
                "losses": stats['battles_lost'],
                "packs": stats['packs_opened'],
                "cards_collected": cards_collected,
                "collection_percentage": collection_percentage
            })

        # Sort users by wins first, then by collection percentage
        users = sorted(
            users,
            key=lambda x: (x['wins'], x['collection_percentage']),
            reverse=True
        )

        # Format leaderboard
        leaderboard = "\n".join(
            [
                f"🥇 {u['username']} - Wins: {u['wins']}, Packs: {u['packs']}, "
                f"Cards Collected: {u['cards_collected']} "
                f"({u['collection_percentage']:.2f}% of total)"
                for u in users
            ]
        ) if users else "No participants this time."

        # Format the final recap
        recap = f"""```yaml\n
    🎉 **{event_name} Event Recap!** 🎉
    The event has ended! Let's check out the highlights:

    📅 **Start Time:** {start_time}
    ⚔️ **Total Battles:** {total_battles}
    🎁 **Packs Opened:** {total_packs}
    🃏 **Cards Pulled:** {total_cards}
    📂 **Total Available Cards:** {total_available_cards}

    🏆 **Trainer Leaderboard (Wins & Card Collection):**  
    {leaderboard}

    Thank you to everyone who participated! Stay tuned for the next event—more battles, more packs, and more Pokémon fun!  
    ```"""
        return recap


