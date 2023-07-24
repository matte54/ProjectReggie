# help command to DM command lists to requesting user.

from systems.logger import log


class Help:
    def __init__(self):
        pass

    async def command(self, message):
        await message.author.send(
            "This is how Woodhouse´s commands work Krappa")

        # this sould probably be a properly formatted file with all information needed
