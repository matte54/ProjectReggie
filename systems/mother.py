from systems.logger import log, debug_on

# We need to consider making a check to make sure woodhouse is allowed to speak in channels we talk to him in
# I wrote a check for this in the reflex task but should be part of all places he is speaking for future proofing.
# Commands should always have the main function in the class called "command" to make this work
# Commands should never return anything? probably


# commands
from systems.commands import (cmd_help, cmd_whoami, cmd_holiday, cmd_remindme, cmd_cast, cmd_blacklist, cmd_seen,
                              cmd_eee, cmd_roll, cmd_event, cmd_define, cmd_fishing, cmd_bucket, cmd_fishbase,
                              cmd_fishoff, cmd_url, cmd_status, cmd_tacklebox, cmd_gamesweek, cmd_fishrules,
                              cmd_fishscore, cmd_b, cmd_stats, cmd_guildstats)


class Mother:
    def __init__(self, client):
        self.client = client
        # commands
        self.remindme = cmd_remindme.Remindme()
        self.event = cmd_event.Event()
        self.help = cmd_help.Help()
        self.holiday = cmd_holiday.Holiday()
        self.whoami = cmd_whoami.Whoami(self.client)
        self.cast = cmd_cast.Cast(self.client)
        self.blacklist = cmd_blacklist.Blacklist()
        self.seen = cmd_seen.Seen(self.client)
        self.eee = cmd_eee.Eee()
        self.roll = cmd_roll.Roll()
        self.define = cmd_define.Define()
        self.fishing = cmd_fishing.Fishing()
        self.tacklebox = cmd_tacklebox.Tacklebox(self.client)
        self.bucket = cmd_bucket.Bucket()
        self.fishoff = cmd_fishoff.Fishoff()
        self.fishbase = cmd_fishbase.Fishbase()
        self.url = cmd_url.Url(self)
        self.status = cmd_status.Status()
        self.gamesweek = cmd_gamesweek.Gamesweek()
        self.fishrules = cmd_fishrules.Fishrules()
        self.fishscore = cmd_fishscore.Fishscore()
        self.b = cmd_b.B(self.client)
        self.stats = cmd_stats.Stats()
        self.guildstats = cmd_guildstats.Guildstats()

        self.cmdlist = {
            "help": self.help,
            "whoami": self.whoami,
            "holiday": self.holiday,
            "remindme": self.remindme,
            "event": self.event,
            "cast": self.cast,
            "blacklist": self.blacklist,
            "seen": self.seen,
            "eee": self.eee,
            "roll": self.roll,
            "define": self.define,
            "fishing": self.fishing,
            "bucket": self.bucket,
            "fishoff": self.fishoff,
            "fishbase": self.fishbase,
            "url": self.url,
            "status": self.status,
            "tacklebox": self.tacklebox,
            "gamesweek": self.gamesweek,
            "fishscore": self.fishscore,
            "b": self.b,
            "stats": self.stats,
            "guildstats": self.guildstats
        }

    async def handle(self, message):
        content = message.content.replace('$', '').lower()
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
