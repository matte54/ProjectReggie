# help command to DM command lists to requesting user.

from systems.logger import log

class Help:
    def __init__(self):
        self.help_str = ""

    async def command(self, message):
        self.help_str = ""
        with open("./data/etc/help.txt", 'r', encoding='utf-8') as f:
            for line in f.readlines():
                self.help_str += line
        log(f'[Help] - {message.author} requested help')

        await message.author.send(f'```yaml\n\n{self.help_str}```')

