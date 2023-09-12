# fishing help
import asyncio
from systems.logger import log

class Fishrules:
    def __init__(self):
        self.help_str = []
        self.current_variable = ""
        self.char_count = 0

    async def command(self, message):
        log(f'[Fishing] - {message.author} requested rules')
        self.help_str = []
        self.current_variable = ""
        self.char_count = 0
        with open("./data/fishing/rules.txt", 'r', encoding='utf-8') as f:
            for line in f.readlines():
                current_line = line
                self.char_count += len(current_line)

                if self.char_count <= 1700:
                    self.current_variable += current_line
                else:
                    # Add the current_variable to the list
                    self.help_str.append(self.current_variable)

                    # Reset char_count and current_variable
                    self.char_count = len(current_line)
                    self.current_variable = current_line

        if self.current_variable:
            self.help_str.append(self.current_variable)

        for item in self.help_str:
            await message.author.send(f'```yaml\n\n{item}```')
            await asyncio.sleep(2)
