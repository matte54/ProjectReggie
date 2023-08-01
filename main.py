# module imports
import asyncio
import discord
import discord.ext
import re
import os
import platform
import random
import datetime

# configs
from data.etc import credentials

# systems
from systems.logger import log, debug_on
from systems.mother import Mother
from systems.housekeeper import HouseKeeper
from systems.speaking import rspeak
from systems.varmanager import VarManager
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
        self.varmanager = VarManager()
        self.unitconverter = Converter()
        self.emojihandler = Emojihandler(self)

        # testing disconnection handling
        self.reconnected = False
        self.last_disconnect = None

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
        await self.housekeeper.cakeday()

    def run_loop(self):
        self.run(credentials.KEY)

    async def on_disconnect(self):
        log(f'Connection LOST!')
        if self.reconnected:
            self.reconnected = False
            self.last_disconnect = datetime.datetime.utcnow()

    async def on_connect(self):
        log(f'Connection ESTABLISHED!')
        self.reconnected = True

    async def on_resumed(self):
        log(f'Connection RE-ESTABLISHED!')
        log(f'Downtime was {datetime.timedelta(seconds=self.total_downtime())}')

    def total_downtime(self):
        if self.last_disconnect is None:
            return 0.0

        return (datetime.datetime.utcnow() - self.last_disconnect).total_seconds()

    async def on_message(self, message):
        try:
            self.prohibited_channels =  self.varmanager.read("black_channels")
        except ValueError:
            pass
        if str(message.channel.id) in self.prohibited_channels:
            # channel is blacklisted do nothing
            log(message) # but log?
            return

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
            await asyncio.sleep(3)
            # added a sleep here, rate limits are easily reached if people are spamming reactions.
            await reaction.message.add_reaction(picked_emoji)

    async def on_guild_emojis_update(self, guild, t1, t2):
        main_channel = guild.text_channels[0]
        # This should be dedicated emojichannel if server does not have one skip.

        set_t1 = set(t1)
        set_t2 = set(t2)

        added_emojis = set_t2 - set_t1
        removed_emojis = set_t1 - set_t2

        if added_emojis:
            for emoji in added_emojis:
                await main_channel.send(f'Emoji {emoji} was added')

        if removed_emojis:
            for emoji in removed_emojis:
                await main_channel.send(f'Emoji {emoji} was removed')


if __name__ == "__main__":
    woodhouse = Woodhouse(intents=intents)
    woodhouse.run_loop()
