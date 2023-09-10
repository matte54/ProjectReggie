import re
import json
import os
import datetime
from systems.logger import log


class Seen:
    def __init__(self, client):
        self.client = client

    async def command(self, message):
        with open("./local/seen.json", "r") as f:
            data = json.load(f)
        log(f'[Seen] - {message.author} - {message.content}')
        matches = re.findall(r'<@(\d+)>', message.content)
        if matches:
            guild = message.guild
            x = guild.get_member(int(matches[0]))
            if str(x.status) == "online":
                await message.channel.send(f'That user is online right now you dummy.')
                return
            if str(matches[0]) in data:
                duration = self.get_duration(data[str(matches[0])])
                await message.channel.send(f'```yaml\n\nI last saw that user {data[str(matches[0])]}\n{duration}```')
                return
        # check usernames instead
        user_search_name = message.content.replace("$seen ", "")
        usernamelist = self.gather_usernames()
        for idnr, username in usernamelist:
            if username == user_search_name.lower():
                guild = message.guild
                x = guild.get_member(int(idnr))
                if str(x.status) == "online":
                    await message.channel.send(f'That user is online right now you dummy.')
                    return
                if str(idnr) in data:
                    duration = self.get_duration(data[str(idnr)])
                    await message.channel.send(f'```yaml\n\nI last saw that user {data[str(idnr)]}\n{duration}```')
                    return

        await message.channel.send(f'Invalid syntax or no data on user')

    def gather_usernames(self):
        usernamelist = []
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                data = json.load(f)
            for key, value in data.items():
                usernamelist.append((key, value.lower()))
        return usernamelist

    def get_duration(self, timestamp):
        time_difference = datetime.datetime.now() - datetime.datetime.fromisoformat(timestamp)

        days = time_difference.days
        seconds = time_difference.seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        result_string = "That was "

        if days > 0:
            result_string += f"{days} days "
        if hours > 0:
            result_string += f"{hours} hours "
        result_string += f"{minutes} minutes ago"
        return result_string
