# help command to DM command lists to requesting user.


# this command has sort of been hijacked as a testbed right now but yeah


from systems.logger import log
from systems.gif_finder import Giphy_find

class Help:
    def __init__(self):
        self.findgif = Giphy_find()

    async def command(self, message):
        x = self.findgif.find("")
        await message.author.send(x)
        #await message.author.send(
        #    "This is how Woodhouse´s commands work Krappa")

        # this sould probably be a properly formatted file with all information needed
