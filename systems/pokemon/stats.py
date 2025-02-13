import json
import os


class TCGStats:
    def __init__(self):
        self.profiles_path = "./local/pokemon/profiles/"

    def stats(self):
        # Initialize stats to track
        stats = {
            "highest_level": [],
            "money": [],
            "best_battlers": [],
            "battles_won": [],
            "battles_lost": [],
            "cards_owned": [],
            "packs_opened": [],
            "valueable_cards": []
        }

        def get_user_name(user_id):
            if os.path.exists(f'./data/etc/ids.json'):
                with open(f'./data/etc/ids.json', "r") as f:
                    id_data = json.load(f)
                if str(user_id) in id_data:
                    return id_data[str(user_id)]

        def update_top_3(stat_list, name, value, decimals=None):
            if decimals is not None:
                value = round(value, decimals)

            stat_list.append({"name": name, "value": value})
            stat_list.sort(key=lambda x: x["value"], reverse=True)
            # Keep only the top 3
            if len(stat_list) > 3:
                stat_list.pop()

        for file_name in os.listdir(self.profiles_path):
            if file_name.endswith(".json"):
                file_path = os.path.join(self.profiles_path, file_name)
                with open(file_path, 'r') as file:
                    try:
                        profile = json.load(file)
                        name = get_user_name(file_name.rsplit(".", 1)[0])
                        profile_data = profile.get("profile", {})

                        # Update stats for each category
                        update_top_3(stats["highest_level"], name, profile_data.get("level", 0))
                        update_top_3(stats["money"], name, profile_data.get("money", 0), decimals=2)
                        update_top_3(stats["battles_won"], name, profile_data.get("battles_won", 0))
                        update_top_3(stats["battles_lost"], name, profile_data.get("battles_lost", 0))
                        update_top_3(stats["cards_owned"], name, profile_data.get("cards", 0))
                        update_top_3(stats["packs_opened"], name, profile_data.get("boosters_opened", 0))

                        # Calculate W/L ratio and update best battler stat
                        battles_won = profile_data.get("battles_won", 0)
                        battles_lost = profile_data.get("battles_lost", 0)
                        if battles_lost > 0:  # Avoid division by zero
                            w_l_ratio = battles_won / battles_lost
                            update_top_3(stats["best_battlers"], name, w_l_ratio, decimals=2)
                        elif battles_won > 0:  # Perfect win record (no losses)
                            update_top_3(stats["best_battlers"], name, float('inf'))

                        # find most valueable card owned
                        highest_value = float('-inf')
                        highest_key = None

                        # Iterate through each nested dictionary in 'sets'
                        for set_name, cards in profile["sets"].items():
                            if cards:  # Check if the dictionary is not empty
                                # Find the key with the maximum value in the current dictionary
                                max_key = max(cards, key=cards.get)
                                max_value = cards[max_key]

                                # Update the highest value and key if this value is larger
                                if max_value > highest_value:
                                    highest_value = max_value
                                    highest_key = max_key
                        setname = highest_key.rsplit("-", 1)[0]
                        with open(f'./data/pokemon/sets/{setname}/{highest_key}.json', 'r') as f:
                            card_data = json.load(f)
                        pokemonname = card_data["name"]
                        update_top_3(stats["valueable_cards"], f'{name} - {pokemonname}({highest_key})', highest_value, decimals=2)

                    except json.JSONDecodeError:
                        print(f"Error decoding {file_name}. Skipping...")

        # Generate a summary report
        report = "```yaml\n\nPokémon Statistics - Top 3:\n"
        for stat, top_players in stats.items():
            report += f"- {stat.replace('_', ' ').title()}:\n"
            for rank, entry in enumerate(top_players, 1):
                report += f"  {rank}. {entry['name']} ({entry['value']})\n"
        report += "```"

        return report
