from systems.logger import log, debug_on

# We need to consider making a check to make sure woodhouse is allowed to speak in channels we talk to him in
# I wrote a check for this in the reflex task but should be part of all places he is speaking for future proofing.
# Commands should always have the main function in the class called "command" to make this work
# Commands should never return anything? probably


# commands
from systems.commands import help, whoami, holiday, remindme, cast, blacklist, seen


class Mother:
    def __init__(self, client):
        self.client = client
        # commands
        self.remindme = remindme.Remindme()
        self.help = help.Help()
        self.holiday = holiday.Holiday()
        self.whoami = whoami.Whoami(self.client)
        self.cast = cast.Cast(self.client)
        self.blacklist = blacklist.Blacklist()
        self.seen = seen.Seen(self.client)

        self.cmdlist = {
            "help": self.help,
            "whoami": self.whoami,
            "holiday": self.holiday,
            "remindme": self.remindme,
            "cast": self.cast,
            "blacklist": self.blacklist,
            "seen": self.seen
        }

    async def handle(self, message):
        content = message.content.replace('$', '')
        firstword = content.split(' ', 1)[0]
        command_function = self.cmdlist.get(firstword)

        if command_function:
            # If the firstword exists in the cmdlist dictionary, call the corresponding command function
            # added the message object into all commands just to make it simple and avoid more if statements
            await command_function.command(message)

        else:
            # Handle the case when the firstword is not recognized
            if debug_on():
                log(f'[Mother] - "{firstword}" is not a valid command')
            await message.channel.send("Invalid Command")
