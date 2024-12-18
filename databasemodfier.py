import os, json
import random


def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def find_json_files(directory):
    json_files = []
    for root, dirs, files in os.walk(directory):  # os.walk traverses directories recursively
        for file in files:
            if file.endswith('.json'):  # Check if the file has a .json extension
                json_files.append(os.path.join(root, file))  # Get the full path
    return json_files


x = find_json_files('./data/pokemon/sets/')

for path in x:
    with open(path, "r") as f:
        data = json.load(f)
    if "prices" not in data["cardmarket"]:
        data["cardmarket"]["prices"] = {}
        randomizedvalue = round(random.uniform(0.50, 10.00), 2)
        data["cardmarket"]["prices"]["averageSellPrice"] = randomizedvalue
        data["cardmarket"]["prices"]["edited"] = "matte"
        write_json(path, data)
        print(f'Updated {path}!')







