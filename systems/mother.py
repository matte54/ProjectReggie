import os
from systems.logger import log, debug_on
from systems.commands import *

# not quite sure how to write this , trying to someone get it to add commands from the command folder and match
# to the incoming messages but i have no clue how to proceed.
# and then seperate commands below for the fishing and pokemons? or maybe not?

class Mother:
    def __init__(self, client):
        self.client = client
        self.commandspath = f'./systems/commands/'
        self.cmdlist = list(map(lambda i: i[: -3], os.listdir("./systems/commands/")))
        log(f"Loading {len(self.cmdlist)} command(s)...")

    def cmdhandle(self, message):
        channel = message.channel
        user = message.author
        content = message.content
        y = content.replace('$', '')

