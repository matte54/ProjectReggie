import os
import asyncio
from systems.logger import log, debug_on

# We need to consider making a check to make sure woodhouse is allowed to speak in channels we talk to him in
# i wrote a check for this in the reflex task but should be part of all places he is speaking for future proofing.

# not quite sure how to write this , trying to someone get it to add commands from the command folder and match
# to the incoming messages but i have no clue how to proceed.
# and then seperate commands below for the fishing and pokemons? or maybe not?

# commands
from systems.commands import help, whoami, holiday, remindme


class Mother:
    def __init__(self, client):
        self.client = client
        self.commandspath = f'./systems/commands/'
        self.cmdlist = list(map(lambda e: e[: -3], os.listdir("./systems/commands/")))
        # added this to stop it from adding pycharms cache folders
        for i in self.cmdlist:
            if i.startswith("__"):
                self.cmdlist.remove(i)
        if debug_on():
            for i in self.cmdlist:
                log(f'[Mother] - [{i}] command loaded!')

        #commands
        self.remindme = remindme.Remindme()
        self.help = help.Help()
        self.holiday = holiday.Holiday()
        self.whoami = whoami.Whoami(self.client)

    async def handle(self, message):
        # there has to be a better way then do the million if statements
        content = message.content.replace('$', '')
        firstword = content.split(' ', 1)[0]
        if firstword in self.cmdlist:
            if firstword == "help":
                x = self.help.command(message)
                return x
            if firstword == "whoami":
                x = self.whoami.command()
                return x
            if firstword == "holiday":
                x = self.holiday.command()
                return x
            if firstword == "remindme":
                x = await self.remindme.command(message)
                return x

        # if content in self.fishcmds:
        #    pass

        # if content in self.pokemoncmds:
        #    pass

        else:
            if debug_on():
                log(f'[ERROR][Mother] - {firstword} is a INVALID command')
