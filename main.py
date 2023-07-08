# module imports
import discord
import discord.ext
import re
import os
import platform

# file imports
from data.etc import credentials
from systems.logger import log, debug_on
from tasks.status import StatusTask
from systems.mother import Mother
from systems.serverinfo import Serverdata
from systems.housekeeper import HouseKeeper

intents = discord.Intents(messages=True, guilds=True, members=True, emojis=True, message_content=True)

if debug_on():
    log("! - DEBUG IS ON - !")

# startup housekeeping
HouseKeeper.logrotate() # rotate chat logs if needed (monthly?)
HouseKeeper.timefiledelete() # delete fishing timefiles


class Woodhouse(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Statustask = None # define task here first cause pycharm thinks so
        self.mother = Mother(self)
        self.serverinfo = Serverdata()
        self.run(credentials.KEY)

    # can this somehow be changed, so it only runs one task that controls all of them (when there are multiple)
    async def setup_hook(self):
        self.Statustask = self.loop.create_task(StatusTask.status_task(self))

    async def on_ready(self):
        log(f"Discord.py API version: {discord.__version__}")
        log(f"Python version: {platform.python_version()}")
        log(f"Running on: {platform.system()} {platform.release()} ({os.name.upper()})")
        log(f'Logged in as {self.user.name} id {self.user.id} - READY!')
        log(f'--------------------------------')

        # on ready housekeeping here
        HouseKeeper.gatherids(self)

    async def on_disconnect(self):
        log(f'Connection LOST to Discord servers!')

    async def on_connect(self):
        log(f'Connection ESTABLISHED to Discord servers!')

    async def on_resumed(self):
        log(f'Connection resumed...')

    async def on_message(self, message):
        if message.channel.type == discord.ChannelType.private:
            # we don't do anything with DMs yet
            return
        if message.author.bot:
            # message came from a bot so do nothing
            return
        log(message)

        # look for $ commands
        if str(message.content).startswith("$"):
            msg = self.mother.handle(message)
        else:
            msg = None
        if msg != None:
            # if the command returns something we need to send it
            await message.channel.send(msg)

        # Rogue´s RE magic to get when someone mentions woodhouse?
        # id and name is for devbot needs to be CHANGED for live.
        sentence, count = re.subn('(?:devbot2000|<@795675666401198101>)', '', message.content, flags=re.IGNORECASE)
        if count:
            await message.channel.send("What´s that?")
            # this leads to the reddit speaking system obvs

    async def on_guild_emojis_update(guild, before, after):
        # automatic emoji change posting? Pog
        pass

    # async def discord.on_reaction_add(reaction, user)
    # woodhouse posting random reactions when someone else does? sometimes? cud be fun.

if __name__ == "__main__":
    woodhouse = Woodhouse(intents=intents)