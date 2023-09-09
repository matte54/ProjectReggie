# module imports
import asyncio
import discord
import discord.ext
import re
import os
import platform
import random
import datetime
import logging

# configs + other
from data.etc import credentials
from data.etc.anoyed import RESPONSES

# systems
from systems.logger import log, debug_on
from systems.mother import Mother
from systems.housekeeper import HouseKeeper
from systems.speaking import Speaking
from systems.varmanager import VarManager
from systems.unitconverter import Converter
from systems.emojihandler import Emojihandler
from systems.statistics import Statistics, Reactionstats
# from systems.newsday import Newsday

# fishing stuff
from systems.fishing.fishoffhandler import Fishoffhandler

# tasks
from tasks.status import StatusTask
from tasks.reflex import Reflex
from tasks.seensaver import SeenSaver
from tasks.event_handler import Event_handler

intents = discord.Intents(messages=True, guilds=True, members=True, emojis=True,
                          message_content=True, reactions=True, presences=True, voice_states=True)

logging.getLogger('discord.gateway').setLevel(30) # trying to get rid of the resumed spam

class Woodhouse(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.prohibited_channels = None

        # tasks
        self.statustask = StatusTask()
        self.reflex = Reflex(self)
        self.seen = SeenSaver(self)
        self.event_handler = Event_handler(self)

        # systems
        self.mother = Mother(self)
        # self.newsday = Newsday(self) # put on hold for now
        self.housekeeper = HouseKeeper(self)
        self.varmanager = VarManager()
        self.unitconverter = Converter()
        self.emojihandler = Emojihandler(self)
        self.statistics = Statistics(self)
        self.reactionstats = Reactionstats(self)
        self.speaking = Speaking()

        # fishing
        self.fishoffhandler = Fishoffhandler(self)

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
        self.loop.create_task(self.seen.seen())
        self.loop.create_task(self.event_handler.track_events())

    async def on_ready(self):
        log(f"Discord.py API version: {discord.__version__}")
        log(f"Python version: {platform.python_version()}")
        log(f"Running on: {platform.system()} {platform.release()} ({os.name.upper()})")
        log(f'Logged in as {self.user.name} id {self.user.id} - READY!')
        log(f'--------------------------------')
        if debug_on():
            log("! - DEBUG IS ON - !")

        # on ready housekeeping
        self.housekeeper.gatherids()
        self.housekeeper.gather_emojis()
        self.housekeeper.clean_logs()
        await self.housekeeper.cakeday()

        # on ready fishing stuff
        await self.fishoffhandler.check_date()  # do the check for fishing season rotate

    def run_loop(self):
        self.run(credentials.KEY)

    async def on_disconnect(self):
        if self.reconnected:
            self.reconnected = False
            self.last_disconnect = datetime.datetime.utcnow()
            # trying this to only say lost if its been over 3 s to stop the spam
            await self.lost_connection()

    async def on_connect(self):
        log(f'Connection ESTABLISHED!')
        self.reconnected = True

    async def lost_connection(self):
        await asyncio.sleep(3)
        if not self.reconnected:
            log(f'Connection LOST!')

    async def on_resumed(self):
        downtime = self.total_downtime()
        if downtime != "0 sec":
            log(f'Connection RE-ESTABLISHED!')
            log(f'Downtime was {downtime}')
        self.last_disconnect = None

    def total_downtime(self):
        if self.last_disconnect is None:
            return "0 sec"

        downtime_seconds = (datetime.datetime.utcnow() - self.last_disconnect).total_seconds()

        # Check if downtime is less than 1 second
        if downtime_seconds < 1:
            return "0 sec"

        minutes = int(downtime_seconds // 60)
        seconds = int(downtime_seconds % 60)

        if minutes == 0:
            return f"{seconds} sec"
        elif minutes == 1:
            return f"1 min {seconds} sec"
        else:
            return f"{minutes} mins {seconds} sec"

    async def on_guild_join(self, guild):
        log(f'ALERT - Woodhouse joined {guild.name}')
        self.housekeeper.gatherids()
        self.housekeeper.gather_emojis()

    async def on_message(self, message):
        if self.varmanager.read("black_channels"):
            self.prohibited_channels = self.varmanager.read("black_channels")
        else:
            self.prohibited_channels = []
        if str(message.channel.id) in self.prohibited_channels:
            # channel is blacklisted do nothing
            if not message.author.bot:
                log(message)  # but log?
            return

        if message.channel.type == discord.ChannelType.private:
            # we don't do anything with DMs yet
            return
        if message.author.bot:
            # message came from a bot so do nothing
            return

        # self.newsday.newsdaylog(message) # log for newsday
        if not str(message.content).startswith("$"):
            log(message)  # send the message into the logs for storing
        self.statistics.input(message)  # send message to stats systems

        # look for $ commands
        if str(message.content).startswith("$"):
            await self.mother.handle(message)

        # look for someone mentioning the bots name
        # the answering and talking works for now but i want to re-write alot of it
        sentence, count = re.subn(f'{self.user.name}|<@{self.user.id}>', '', message.content, flags=re.IGNORECASE)
        if count:
            sentence.replace('  ', '')
            if not sentence:
                i = random.choice(RESPONSES)
            else:
                i, debugmsg = await self.speaking.process_input(sentence)
                # emoji fallback if none
                if not i:
                    i = self.emojihandler.emojihandler(message.channel.id)
                if message.guild.id == 194028816333537280:
                    # if guild darkzone do the debug stuff member
                    debugchannel = self.get_channel(1007604139657789470)
                    if debugmsg:
                        await debugchannel.send(f'```yaml\n\n{debugmsg}```')
            await message.channel.send(i)

        # check for conversions for unitconverter
        await self.unitconverter.check(message)

    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        self.reactionstats.handle_reactions(reaction, user)
        # If woodhouse sees someone add a reaction , 25% chance of him adding one to.
        reacted_channel_id = reaction.message.channel.id
        if random.random() < 0.10:
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

    async def on_voice_state_update(self, member, before, after):
        pass
        # keep track of time in voice chat later maybe hmm


if __name__ == "__main__":
    woodhouse = Woodhouse(intents=intents)
    woodhouse.run_loop()
