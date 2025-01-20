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
            "battles_won": [],
            "battles_lost": [],
            "cards_owned": [],
            "packs_opened": []
        }

        def get_user_name(user_id):
            if os.path.exists(f'./data/etc/ids.json'):
                with open(f'./data/etc/ids.json', "r") as f:
                    id_data = json.load(f)
                if str(user_id) in id_data:
                    return id_data[str(user_id)]

        def update_top_3(stat_list, name, value):
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
                        update_top_3(stats["money"], name, profile_data.get("money", 0))
                        update_top_3(stats["battles_won"], name, profile_data.get("battles_won", 0))
                        update_top_3(stats["battles_lost"], name, profile_data.get("battles_lost", 0))
                        update_top_3(stats["cards_owned"], name, profile_data.get("cards", 0))
                        update_top_3(stats["packs_opened"], name, profile_data.get("boosters_opened", 0))

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
