# roll dice

import random
import re
from systems.logger import log

class Roll:
    def __init__(self):
        self.pattern = r'(\d{1,2})d(\d{1,2})'
        self.dice = None
        self.result = 0


    async def command(self, message):
        log(f'[Roll] - {message.author} - Rolls dice(s)')
        matches = re.findall(self.pattern, message.content)
        if len(matches) == 1:
            self.dice = matches[0]
            for dice in range(int(self.dice[0])):
                self.result += random.randint(1, int(self.dice[1]))

            await message.channel.send(f'```yaml\n\n{message.author} rolls {self.dice[0]}d{self.dice[1]} and it turned up {self.result}```')
            self.result = 0
            return

        await message.channel.send(f'```yaml\n\nSyntax error, usage is XdX, x:es being how many dices and how many sides```')
