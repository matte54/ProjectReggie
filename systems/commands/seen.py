import re
import json
from systems.logger import log

class Seen:
    def __init__(self, client):
        self.client = client

    async def command(self, message):
        log(f'[Seen] - {message.author} - {message.content}')
        matches = re.findall(r'<@(\d+)>', message.content)
        if matches:
            guild = message.guild
            x = guild.get_member(int(matches[0]))
            if str(x.status) == "online":
                await message.channel.send(f'That user is online right now you dummy.')
                return
            with open("./local/seen.json", "r") as f:
                data = json.load(f)
            if str(matches[0]) in data:
                await message.channel.send(f'I last saw that user {data[str(matches[0])]}')
                return
        await message.channel.send(f'Invalid syntax or no data on user')


