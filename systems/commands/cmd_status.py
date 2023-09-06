import re
import json
from systems.logger import log


class Status:
    def __init__(self):
        self.file_path = "./data/etc/statuses.json"

    async def command(self, message):
        with open(self.file_path, "r") as f:
            status_dict = json.load(f)
        msg = message.content.replace("$status ", "")
        processed_str, status_type = self.process_string(msg)
        # returns None, None if theres a problem
        # returns string, type if adding
        # returns Int, rm if deleting
        if processed_str is None and status_type is None:
            message.channel.send("Something went wrong.")
            return
        if isinstance(processed_str, int) and status_type == "rm":
            return_answer = self.delete_entry(str(processed_str), status_dict)
            if return_answer:
                log(f'[Status] - {message.author} {return_answer}')
                await message.channel.send(f'```yaml\n\n{return_answer}```')
                return
            else:
                await message.channel.send(f'```yaml\n\nID number not found```')
                return

        # from here we only add stuff
        highest_id_nr = self.find_last_id(status_dict)
        if not highest_id_nr: # if theres no entries start at 1
            highest_id_nr = 1
        else:
            highest_id_nr += 1

        return_answer = self.add_entry(str(highest_id_nr), status_type, processed_str, status_dict)
        log(f'[Status] - {message.author} added status #{highest_id_nr}')
        await message.channel.send(f'```yaml\n\n{return_answer}```')

    def add_entry(self, id_nr, status_type, status_string, status_dict):
        status_dict[status_type][id_nr] = status_string
        self.write_json(self.file_path, status_dict)
        return f'Added status #{id_nr}!'

    def delete_entry(self, id_nr, status_dict):
        for key in status_dict["playing"]:
            if id_nr in status_dict["playing"]:
                del status_dict["playing"][key]
                self.write_json(self.file_path, status_dict)
                return f"Status #{id_nr} deleted!"
        for key in status_dict["watching"]:
            if id_nr in status_dict["watching"]:
                del status_dict["watching"][key]
                self.write_json(self.file_path, status_dict)
                return f"Status #{id_nr} deleted!"
        for key in status_dict["listening"]:
            if id_nr in status_dict["listening"]:
                del status_dict["listening"][key]
                self.write_json(self.file_path, status_dict)
                return f"Status #{id_nr} deleted!"

        return None


    def find_last_id(self, status_dict):
        highest_key = None

        for key, value in status_dict.items():
            if key.isdigit():
                int_key = int(key)
                if highest_key is None or int_key > highest_key:
                    highest_key = int_key

            if isinstance(value, dict):
                nested_highest_key = self.find_last_id(value)
                if nested_highest_key is not None and (highest_key is None or nested_highest_key > highest_key):
                    highest_key = nested_highest_key

        return highest_key

    def process_string(self, msg):
        if msg.startswith("add"):
            wordlist = msg.split()
            if len(wordlist) > 1:
                if wordlist[1] == "playing":
                    status_string = ' '.join(wordlist[2:])
                    if len(status_string) > 60:
                        return None, None
                    return status_string, "playing"
                elif wordlist[1] == "watching":
                    status_string = ' '.join(wordlist[2:])
                    if len(status_string) > 60:
                        return None, None
                    return status_string, "watching"
                elif wordlist[1] == "listening":
                    status_string = ' '.join(wordlist[2:])
                    if len(status_string) > 60:
                        return None, None
                    return status_string, "listening"
                else:
                    return None, None
            else:
                return None, None

        elif msg.startswith("rm"):
            matches = re.findall(r'\b\d{1,4}\b', msg)
            if matches:
                return int(matches[0]), "rm"
            else:
                return None, None
        else:
            # invalid command
            return None, None

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)