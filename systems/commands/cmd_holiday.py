import random
import requests
from lxml import etree as et
from systems.logger import log

class Holiday:
    def __init__(self):
        pass

    async def command(self, message):
        log(f'[Holiday] - {message.author} - Holiday')
        req = requests.get('https://www.checkiday.com/rss.php?tz=Europe/Stockholm')
        result = et.fromstring(req.content)
        things = [thing[1].text for thing in result.iter('item')]

        await message.channel.send(random.choice(things))
