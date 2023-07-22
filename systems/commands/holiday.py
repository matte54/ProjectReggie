import random
import requests
from lxml import etree as et


class Holiday:
    def __init__(self):
        pass
    def command(self):
        req = requests.get('https://www.checkiday.com/rss.php?tz=Europe/Stockholm')
        result = et.fromstring(req.content)
        things = [thing[1].text for thing in result.iter('item')]
        return random.choice(things)
