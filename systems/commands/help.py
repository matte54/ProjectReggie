# help command to DM command lists to requesting user.


# this command has sort of been hijacked as a testbed right now but yeah


from systems.logger import log
from systems.gif_finder import Giphy_find

class Help:
    def __init__(self):
        pass

    async def command(self, message):
        print(message.author.status)
        print(message.author.desktop_status)
        print(message.author.mobile_status)
        print(message.author.web_status)
        #await message.author.send(
        #    "This is how Woodhouse´s commands work Krappa")

        # this sould probably be a properly formatted file with all information needed
