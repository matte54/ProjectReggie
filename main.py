# module imports
import asyncio
import discord
import discord.ext
import re
import os
import platform
import random

# configs
from data.etc import credentials

# systems
from systems.logger import log, debug_on
from systems.mother import Mother
from systems.housekeeper import HouseKeeper
from systems.speaking import rspeak
from systems.filemanager import VarManager
from systems.unitconverter import Converter
from systems.emojihandler import Emojihandler

# tasks
from tasks.status import StatusTask
from tasks.reflex import Reflex

intents = discord.Intents(messages=True, guilds=True, members=True, emojis=True, message_content=True, reactions=True)

if debug_on():
    log("! - DEBUG IS ON - !")


class Woodhouse(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # tasks
        self.statustask = StatusTask()
        self.reflex = Reflex(self)

        # systems
        self.mother = Mother(self)
        self.housekeeper = HouseKeeper(self)
        self.varmanger = VarManager()
        self.unitconverter = Converter()
        self.emojihandler = Emojihandler(self)

        self.run(credentials.KEY)

    # can this somehow be changed, so it only runs one task that controls all of them (when there are multiple)
    # been sort of looking at the cogs there are some stuff about the tasks system that built can keep an eye
    # on time and scheduling for background tasks etc. i dunno should probably look more into that before
    # evovling more complex taasks
    async def setup_hook(self):
        self.loop.create_task(self.statustask.status_task(self))
        self.loop.create_task(self.reflex.reflex())

    async def on_ready(self):
        log(f"Discord.py API version: {discord.__version__}")
        log(f"Python version: {platform.python_version()}")
        log(f"Running on: {platform.system()} {platform.release()} ({os.name.upper()})")
        log(f'Logged in as {self.user.name} id {self.user.id} - READY!')
        log(f'--------------------------------')

        # on ready housekeeping
        self.housekeeper.gatherids()
        self.housekeeper.gather_emojis()

        # testing varmanager (working)
        # test = self.varmanger.read("testvar")
        # self.varmanger.write("stuff", ["bananas", "apples"])

    async def on_disconnect(self):
        log(f'Connection LOST!')

    async def on_connect(self):
        log(f'Connection ESTABLISHED!')

    async def on_resumed(self):
        log(f'Connection RE-ESTABLISHED!')

    async def on_message(self, message):
        if message.channel.type == discord.ChannelType.private:
            # we don't do anything with DMs yet
            return
        if message.author.bot:
            # message came from a bot so do nothing
            return

        log(message)  # send the message into the logs for storing

        # look for $ commands
        if str(message.content).startswith("$"):
            await self.mother.handle(message)

        # look for someone mentioning the bots name
        # the answering and talking works for now but i want to re-write alot of it
        sentence, count = re.subn(f'{self.user.name}|<@{self.user.id}>', '', message.content, flags=re.IGNORECASE)
        if count:
            sentence.replace('  ', '')
            if not sentence:
                i = "stop that!"
            else:
                i, debugstuff = rspeak(sentence)
            # debugchannel = self.get_channel(1007604139657789470) #debugchannel addition
            # await debugchannel.send(debugstuff)
            await message.channel.send(i)

        # check for conversions for unitconverter
        await self.unitconverter.check(message)

    async def on_reaction_add(self, reaction, user):
        # If woodhouse sees someone add a reaction , 25% chance of him adding one to.
        reacted_channel_id = reaction.message.channel.id
        if random.random() < 0.25:
            picked_emoji = self.emojihandler.emojihandler(reacted_channel_id)
            await reaction.message.add_reaction(picked_emoji)
            await asyncio.sleep(3)
            # added a sleep here, rate limits are easily reached if people are spamming reactions.


if __name__ == "__main__":
    woodhouse = Woodhouse(intents=intents)
