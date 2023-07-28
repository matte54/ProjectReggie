import json
import os


# create fish
# name=str, joke=str, min_weight=float, max_weight=float, value=int, xp=int, rarity=float(0-1), unique=bool, group=int(class 1-7)


def make_fish(name, joke, min_weight, max_weight, value, xp, rarity, unique, group):
    if os.path.isfile(f'./class{group}.json'):
        with open(f'./class{group}.json', "r") as f:
            data = json.load(f)

        if name in data:
            print("Fish already exists")
            return

        data[name] = {}
        data[name]["joke"] = joke
        data[name]["min_weight"] = min_weight
        data[name]["max_weight"] = max_weight
        data[name]["value"] = value
        data[name]["xp"] = xp
        data[name]["rarity"] = rarity
        data[name]["unique"] = unique

        write_json(f'./class{group}.json', data)

    else:
        fish = {
            name:
                {
                    "joke": joke,
                    "min_weight": min_weight,
                    "max_weight": max_weight,
                    "value": value,
                    "xp": xp,
                    "rarity": rarity,
                    "unique": unique
                }
        }
        write_json(f'./class{group}.json', fish)


def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


make_fish("Tin can",
          "This can can!",
          0.10,
          0.2,
          1,
          1,
          0.05,
          False,
          1)
