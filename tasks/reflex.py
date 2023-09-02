# Background task for woodhouses spontanous actions

import asyncio
import random
import os
from datetime import datetime, timedelta

from systems.logger import log, debug_on
from systems.speaking import Speaking
from systems.emojihandler import Emojihandler
from systems.varmanager import VarManager
from systems.gif_finder import Giphy_find


# list of channels ids woodhouse cannot reflex in


class Reflex:
    def __init__(self, client):
        print("Reflex initilizated!")
        self.client = client
        self.emojihandler = Emojihandler(self.client)
        self.wait_cycles = 1
        self.guild_list = []
        self.numbers = [0, 1, 2, 3, 4, 5, 6]
        self.random_weights = [10, 9, 8, 4, 4, 2, 10]
        self.varmanager = VarManager()
        self.speaking = Speaking()
        self.gif_finder = Giphy_find()
        self.prohibited_channels = []

    # main loop
    async def reflex(self):
        print("Starting reflex loop")
        #await self.client.wait_until_ready()
        await asyncio.sleep(10)
        await self.find_guilds()
        while True:
            if self.varmanager.read("black_channels"):
                self.prohibited_channels = self.varmanager.read("black_channels")
            else:
                self.prohibited_channels = []

            channel_list = self.find_channel()  # get all channels to work with
            # filter out channels with these functions
            channel_list = await self.wasitme(channel_list)  # remove channels not suitable
            if channel_list:
                channel_list = await self.channel_history(channel_list)  # remove dead channels
            if channel_list:
                if debug_on():
                    log(f'[Reflex] - Available channels: {channel_list}')
                picked_channel = random.choice(channel_list)
                # random a reflex action with weights
                k = random.choices(self.numbers, weights=self.random_weights)
                # k = [4] # this is left here to specifiy a choice for debugging
                # If we random nothing or if theres no channels to do anything in
                if k[0] == 0:
                    log(f'[Reflex] - DO NOTHING - {picked_channel}')
                    self.wait_cycles = 1
                # talk
                if k[0] == 1:
                    log(f'[Reflex] - TALK - {picked_channel}')
                    last_message = await self.find_message(picked_channel,
                                                           10)  # get the last message in the chosen channel
                    self.wait_cycles += 1
                    await self.talk(picked_channel, last_message)
                # reaction
                if k[0] == 2:
                    log(f'[Reflex] - REACTION - {picked_channel}')
                    last_message = await self.find_message(picked_channel,
                                                           1)  # get the last message in the chosen channel
                    self.wait_cycles += 1
                    await self.reaction(picked_channel, last_message)
                # reply
                if k[0] == 3:
                    log(f'[Reflex] - REPLY - {picked_channel}')
                    last_message = await self.find_message(picked_channel,
                                                           1)  # get the last message in the chosen channel
                    self.wait_cycles += 1
                    await self.reply(last_message)
                # url
                if k[0] == 4:
                    log(f'[Reflex] - URL - {picked_channel}')
                    self.wait_cycles += 2
                    await self.url(picked_channel)
                # recommend
                if k[0] == 5:
                    log(f'[Reflex] - RECOMMEND - {picked_channel}')
                    self.wait_cycles += 2
                    self.recommend(picked_channel)
                # do nothing
                if k[0] == 6:
                    self.wait_cycles += 1
                    log(f'[Reflex] - Waiting...')

            await asyncio.sleep((60 * random.randint(30, 40)) * self.wait_cycles)  # use this formula for live

    async def channel_history(self, channel_list):
        # check channel history for recent activity to rule out dead channels
        # i think this works, im not quite sure how the around datetime stuff
        refined_list = []
        for i in channel_list:
            channel = self.client.get_channel(i)
            async for message in channel.history(limit=5):
                if not message.author.bot:
                    diffrence = datetime.now() - message.created_at.replace(tzinfo=None)
                    if not diffrence > timedelta(days=1):
                        log(f'[Reflex] - {i} has a message today')
                        refined_list.append(i)
                        break
        return refined_list

    def check_logs(self):
        # checks log folder and picks something someone said and returns it if nothing found returns None
        line = ""
        matching_files = []
        for root, _, files in os.walk("./log"):
            for file in files:
                if file.endswith("log"):
                    matching_files.append(os.path.join(root, file))
        if matching_files:
            logfile = random.choice(matching_files)
            with open(logfile, 'r', encoding='utf-8') as f:
                line = random.choice(f.readlines())
        return line

    async def wasitme(self, channel_list):
        # this only works if we make a new list, dosent like if i remove things from the list when i loop
        # check all channels if Woodhouse was the last person to say something, if so remove the channel
        refined_list = []
        for i in channel_list:
            channel = self.client.get_channel(i)
            async for message in channel.history(limit=1):
                if message.author != self.client.user:
                    refined_list.append(i)
        if not refined_list:
            log(f'[Reflex] - All available channels has last message by Woodhouse')
        return refined_list

    async def find_guilds(self):
        # find servers woodhouse is in
        for guild in self.client.guilds:
            self.guild_list.append(guild)

    def find_channel(self):
        # find channels woodhouse is in and is allowed to speak in (all servers)
        channel_list = []
        for guild in self.guild_list:
            for channel in guild.text_channels:
                if channel.permissions_for(
                        guild.get_member(self.client.user.id)).send_messages and str(
                    channel.id) not in self.prohibited_channels:
                    channel_list.append(channel.id)
        return channel_list

    # find the last message in the picked channel
    async def find_message(self, picked_channel, nr_of_messages):
        msg_list = []
        channel = self.client.get_channel(picked_channel)
        # pycharm does not like this double return thing but it works
        async for message in channel.history(limit=nr_of_messages):
            if nr_of_messages > 1:
                msg_list.append(message)
        if nr_of_messages > 1:
            return msg_list

        return message

    async def talk(self, picked_channel, last_message):
        # random nonsense based on last messsages in the channel
        # gets a list of the last 10 messages instead of just 1 object
        last_message = random.choice(last_message)
        channel = self.client.get_channel(picked_channel)
        last_message_content = last_message.content
        if random.uniform(0.0, 1.0) < 0.25:
            txt = self.check_logs()
            if not txt:
                txt, debugmsg = await self.speaking.process_input(last_message_content)
        else:
            txt, debugmsg = await self.speaking.process_input(last_message_content)
        await channel.send(txt)

    async def reaction(self, picked_channel, last_message):
        # adds reaction to last message, skip if already reacted
        x = last_message.reactions
        if not x:
            picked_emoji = self.emojihandler.emojihandler(picked_channel)
            await last_message.add_reaction(picked_emoji)
        else:
            if debug_on():
                log(f'[Reflex] - Already reacted to this message')

    async def reply(self, last_message):
        # replies on last message sent in selected channel
        last_message_content = last_message.content
        if random.uniform(0.0, 1.0) < 0.25:
            txt = self.check_logs()
            if not txt:
                txt, debugmsg = await self.speaking.process_input(last_message_content)
        else:
            txt, debugmsg = await self.speaking.process_input(last_message_content)
        await last_message.reply(txt)

    async def url(self, picked_channel):
        # for now this just uses the giphy trending stuff
        # scraper should be implemented here at some point
        channel = self.client.get_channel(picked_channel)
        gif = self.gif_finder.find("")
        if gif:
            await channel.send(gif)

    def recommend(self, picked_channel):
        pass
