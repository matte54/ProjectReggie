# Background task for woodhouses spontanous actions

import random
import asyncio
import discord
from datetime import datetime

from systems.logger import log, debug_on
from systems.speaking import rspeak

# list of channels ids woodhouse cannot reflex in
prohibited_channels = []


class Reflex:
    def __init__(self, client):
        self.client = client
        self.wait_cycles = 0
        self.guild_list = []
        self.numbers = [0, 1, 2, 3, 4, 5]
        self.random_weights = [10, 9, 8, 6, 4, 2]

    # main loop
    async def reflex(self):
        await self.client.wait_until_ready()
        self.find_guilds()

        while True:
            channel_list = self.find_channel()  # get all channels to work with
            # filter out channels with these functions
            channel_list = await self.wasitme(channel_list)  # remove channels not suitable
            channel_list = await self.channel_history(channel_list)  # remove dead channels
            if debug_on():
                log(f'[Reflex] - FINAL channel list: {channel_list}')
            picked_channel = random.choice(channel_list)
            if picked_channel is not None:
                last_message = await self.find_message(picked_channel) # get the last message in the chosen channel
                # random a reflex action with weights
                #k = random.choices(self.numbers, weights=self.random_weights)
                k = [1]
                # If we random nothing or if theres no channels to do anything in
                if k[0] == 0 or k is None:
                    log(f'[Reflex] - do nothing')
                    self.wait_cycles = 0
                # talk
                if k[0] == 1:
                    log(f'[Reflex] - talk')
                    self.wait_cycles += 1
                    await self.talk(picked_channel, last_message)
                # reaction
                if k[0] == 2:
                    log(f'[Reflex] - reaction')
                    self.wait_cycles += 1
                    self.reaction(picked_channel, last_message)
                # reply
                if k[0] == 3:
                    log(f'[Reflex] - reply')
                    self.wait_cycles += 1
                    self.reply(picked_channel, last_message)
                # url
                if k[0] == 4:
                    log(f'[Reflex] - url')
                    self.wait_cycles += 2
                    self.url(picked_channel)
                # recommend
                if k[0] == 5:
                    log(f'[Reflex] - recommend')
                    self.wait_cycles += 2
                    self.recommend(picked_channel)

            # await asyncio.sleep((60 * random.randint(30, 60)) * self.wait_cycles) # use this formula for live
            await asyncio.sleep(10)

    async def channel_history(self, channel_list):
        # check channel history for recent activity to rule out dead channels
        for i in channel_list:
            number_of_messages = 0
            channel = self.client.get_channel(i)
            async for x in channel.history(limit=10, around=datetime.utcnow()):
                number_of_messages += 1
            if debug_on():
                log(f'[Reflex] - {i} has {number_of_messages} message(s) today')
            # if channel has no messages today remove it from the list.
            if number_of_messages < 1:
                channel_list.remove(i)
        return channel_list

    async def wasitme(self, channel_list):
        # check all channels if Woodhouse was the last person to say something, if so remove the channel
        for i in channel_list:
            channel = self.client.get_channel(i)
            async for message in channel.history(limit=1):
                if message.author == self.client.user:
                    channel_list.remove(i)
        return channel_list

    def find_guilds(self):
        # find servers woodhouse is in
        for guild in self.client.guilds:
            self.guild_list.append(guild)

    def find_channel(self):
        # find channels woodhouse is in and is allowed to speak in (all servers)
        channel_list = []
        for guild in self.guild_list:
            for channel in guild.text_channels:
                if channel.permissions_for(
                        guild.get_member(self.client.user.id)).send_messages and channel.id not in prohibited_channels:
                    channel_list.append(channel.id)
        return channel_list

    # find the last message in the picked channel
    async def find_message(self, picked_channel):
        channel = self.client.get_channel(picked_channel)
        async for message in channel.history(limit=1):
            return message

    async def talk(self, picked_channel, last_message):
        # random nonsense based on last messsage in the channel
        channel = self.client.get_channel(picked_channel)
        last_message_content = last_message.content
        txt , debugstuff = rspeak(last_message_content)
        await channel.send(txt)

    def reaction(self, picked_channel, last_message):
        pass

    def reply(self, picked_channel, last_message):
        pass

    def url(self, picked_channel):
        pass

    def recommend(self, picked_channel):
        pass
