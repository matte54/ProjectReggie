import json
import os


def make_mon(name, n_id, m_type, rarity, stage, hp, attack, defense, sp_atk, sp_def, speed, xp, rate):
    if os.path.isfile(f'./database.json'):
        with open(f'./database.json', "r") as f:
            data = json.load(f)

        if name in data:
            print("Mon already exists")
            return

        data[name] = {}
        data[name]["n_id"] = n_id
        data[name]["type"] = m_type
        data[name]["rarity"] = rarity
        data[name]["stage"] = stage
        data[name]["hp"] = hp
        data[name]["attack"] = attack
        data[name]["defense"] = defense
        data[name]["sp_atk"] = sp_atk
        data[name]["sp_def"] = sp_def
        data[name]["speed"] = speed
        data[name]["xp"] = xp
        data[name]["rate"] = rate

        write_json(f'./database.json', data)


def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


make_mon("Bulbasaur",  # Name (str)
         1,  # National No (int)
         [5, 6],  # Type (list(int))
         0,  # Rarity (int) common 0, uncommon 1, rare 2
         0,  # Evolution stage (int) 0-2
         40,  # HP (int)
         49,  # Attack (int)
         49,  # Defense (int)
         65,  # Sp. Atk (int)
         65,  # Sp. Def (int)
         45,  # Speed (int)
         64,  # Xp (int)
         3)  # Growth rate (int) 0-5 erratic, fast, mfast, mslow, slow, fluctuating
