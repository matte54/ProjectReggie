import json
import os
import string
import random


# create fish
# name=str, joke=str, min_weight=float, max_weight=float, value=int, xp=int, rarity=float(0-1), unique=bool, group=int(class 1-7)


def make_fish(name, joke, min_weight, max_weight, value, xp, rarity, unique, group, id):
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
        data[name]["id"] = id

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
                    "unique": unique,
                    "id": id
                }
        }
        write_json(f'./class{group}.json', fish)

    with open("./usedids.txt", "a", encoding='utf8')as f:
        f.write(f'{id}\n')



def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def gen_id():
    with open("./usedids.txt", encoding='utf8')as f:
        usedids = f.read().splitlines()

    found_unused_id = False
    while not found_unused_id:
        id_generated = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(6))
        if not id_generated in usedids:
            found_unused_id = True
    return id_generated


x = f'f{str(gen_id())}'
make_fish("Arapaima",
          "How did it get here? Arapaiknow!",
          6.0,
          2440.0,
          7,
          7,
          0.1,
          False,
          7,
          x)


# name=str, joke=str, min_weight=float, max_weight=float, value=int, xp=int, rarity=float(0-1), unique=bool, group=int(class 1-7)