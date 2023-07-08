import os
from systems.logger import log, debug_on

# not quite sure how to write this , trying to someone get it to add commands from the command folder and match
# to the incoming messages but i have no clue how to proceed.
# and then seperate commands below for the fishing and pokemons? or maybe not?

# commands
from systems.commands import help, whoami, holiday


class Mother:
    def __init__(self, client):
        self.client = client
        self.commandspath = f'./systems/commands/'
        self.cmdlist = list(map(lambda i: i[: -3], os.listdir("./systems/commands/")))
        # added this to stop it from adding pycharms cache folders
        for i in self.cmdlist:
            if i.startswith("__"):
                self.cmdlist.remove(i)
        if debug_on():
            for i in self.cmdlist:
                log(f'[INFO] [{i}] command loaded!')

    def handle(self, message):
        content = message.content.replace('$', '')

        # there has to be a better way then do the million if statements
        if content in self.cmdlist:
            if content == "help":
                x = help.Help.command(message)
                return x
            if content == "whoami":
                x = whoami.Whoami.command(self.client)
                return x
            if content == "holiday":
                x = holiday.Holiday.command()
                return x


        #if content in self.fishcmds:
        #    pass

        #if content in self.pokemoncmds:
        #    pass

        else:
            if debug_on():
                log(f'{content} is a INVALID command')
