# handler that reads the emojis.json, checks if woodhouse can use it in the server
# and hopefully some sort of logic to go with the choice.

import json
import random


class Emojihandler:
    def __init__(self, client):
        self.client = client

    # this function needs the channelid of where its going to be used
    def emojihandler(self, channelid):
        # get guild id from channelid
        channel = self.client.get_channel(channelid)
        guildid = channel.guild.id

        with open("./local/emojis.json", "r") as f:
            data = json.load(f)

        if bool(random.getrandbits(1)):
            # default emojis
            emojilist = data["default"]
        else:
            # custom emojis
            emojilist = data[str(guildid)]

        return random.choice(emojilist)
