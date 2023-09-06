from systems.logger import log

class Eee:
    def __init__(self):
        pass

    async def command(self, message):
        log(f'[Eee] - {message.author} casts a sunstrike!')
        await message.channel.send("SUNSTRIKE! (ノಠ益ಠ)ノ彡 !!!(°Д°)!!!")
