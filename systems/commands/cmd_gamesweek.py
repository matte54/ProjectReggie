import json
from systems.logger import log


class Gamesweek:
    def __init__(self):
        pass

    async def command(self, message):
        with open("./systems/games_weekly/weeks_videogames.json", "r") as f:
            data = json.load(f)

        list_string = "---- VIDEOGAME RELEASES THIS WEEK ----\n"

        for key, value in data.items():
            list_string += f'* {key} *\n'
            list_string += f'{value["platform"]}\n'
            list_string += f'{value["release"]}\n\n'

        await message.channel.send(f'```yaml\n\n{list_string}```')
