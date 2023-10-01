from systems.logger import log
from systems.varmanager import VarManager

class Fishscore:
    def __init__(self):
        self.varmanager = VarManager()
        self.scorefile = "./local/fishing/fishoff_history.txt"
        self.line_limit = 12

    async def command(self, message):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            if message.channel.id in fishing_channels:
                end_line = f"* * * Seasonal winner history(last {self.line_limit}) * * *\n"
                log(f'[Fishing] - {message.author} listing highscores')
                with open(self.scorefile, 'r', encoding='utf-8') as f:
                    i = 0
                    for line in f.readlines():
                        end_line += line
                        i += 1
                        if i >= self.line_limit:
                            break

                await message.channel.send(f'```yaml\n\n{end_line}```')
