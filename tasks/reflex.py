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
from systems.urlhandler import Urlhandler


# list of channels ids woodhouse cannot reflex in


class Reflex:
    def __init__(self, client):
        self.client = client
        self.emojihandler = Emojihandler(self.client)
        self.wait_cycles = 1
        self.guild_list = []
        self.numbers = [0, 1, 2, 3, 4, 5, 6]
        self.random_weights = [10, 9, 8, 4, 4, 2, 10]
        self.increased_weights = [5, 6, 6, 6, 6, 6, 5]
        self.varmanager = VarManager()
        self.urlhandler = Urlhandler(self.client)
        self.speaking = Speaking()
        self.gif_finder = Giphy_find()
        self.prohibited_channels = []

    # main loop
    async def reflex(self):
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
                log(f'[Reflex] - Available channels: {len(channel_list)}')
                picked_channel = random.choice(channel_list)
                # random a reflex action with weights (if theres more then 5 channels to chose from increase chance)
                if len(channel_list) > 5:
                    reflex_choice = random.choices(self.numbers, weights=self.increased_weights)
                else:
                    reflex_choice = random.choices(self.numbers, weights=self.random_weights)
                # reflex_choice = [2] # this is left here to specifiy a choice for debugging

                if reflex_choice[0] == 0:
                    log(f'[Reflex] - DO NOTHING - {picked_channel}')
                    self.wait_cycles += 1
                # talk
                if reflex_choice[0] == 1:
                    log(f'[Reflex] - TALK - {picked_channel}')
                    last_message = await self.find_message(picked_channel,
                                                           10)  # get the last message in the chosen channel
                    self.wait_cycles = 1
                    await self.talk(picked_channel, last_message)
                    self.prohibited_channels.append(picked_channel)
                # reaction
                if reflex_choice[0] == 2:
                    log(f'[Reflex] - REACTION - {picked_channel}')
                    last_message = await self.find_message(picked_channel,
                                                           1)  # get the last message in the chosen channel
                    self.wait_cycles = 1
                    await self.reaction(picked_channel, last_message)
                # reply
                if reflex_choice[0] == 3:
                    # turned off for now , thought it was gonna be fun but feels mostly annoying
                    log(f'[Reflex] - REPLY - {picked_channel}')
                    #last_message = await self.find_message(picked_channel,
                    #                                       1)  # get the last message in the chosen channel
                    self.wait_cycles = 1
                    #await self.reply(picked_channel, last_message)
                # url
                if reflex_choice[0] == 4:
                    log(f'[Reflex] - GIF - {picked_channel}')
                    self.wait_cycles = 2
                    await self.gif(picked_channel)
                    self.prohibited_channels.append(picked_channel)
                # recommend
                if reflex_choice[0] == 5:
                    log(f'[Reflex] - URL - {picked_channel}')
                    self.wait_cycles = 2
                    await self.url(picked_channel)
                    self.prohibited_channels.append(picked_channel)
                # do nothing
                if reflex_choice[0] == 6:
                    self.wait_cycles = 1
                    log(f'[Reflex] - Waiting...')

            else:
                log(f'[Reflex] - No valid channels, waiting...')
                self.wait_cycles += 1


            sleep_time = (120 * random.randint(30, 40)) * self.wait_cycles
            log(f'[Reflex] - Sleeping {round(sleep_time / 60)} minutes')
            await asyncio.sleep(sleep_time)

    async def channel_history(self, channel_list):
        # check channel history for recent activity to rule out dead channels
        # i think this works, im not quite sure how the around datetime stuff
        refined_list = []
        for i in channel_list:
            channel = self.client.get_channel(i)
            async for message in channel.history(limit=5):
                if not message.author.bot:
                    diffrence = datetime.now() - message.created_at.replace(tzinfo=None)
                    if not diffrence > timedelta(hours=3):
                        log(f'[Reflex] - {i} - ({channel.guild.name}:{channel.name}) has recent activity')
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
            if nr_of_messages == 1:
                return message
            if nr_of_messages > 1:
                msg_list.append(message)

        return msg_list

    async def talk(self, picked_channel, last_message):
        channel = self.client.get_channel(picked_channel)
        # random nonsense based on last messsages in the channel
        # gets a list of the last 10 messages instead of just 1 object
        if not last_message:
            log(f'[Reflex] - No proper messages to use, emoji backup')
            picked_emoji = self.emojihandler.emojihandler(picked_channel)
            await channel.send(picked_emoji)
            return
        last_message = random.choice(last_message)
        last_message_content = last_message.content
        if random.uniform(0.0, 1.0) < 0.25:
            txt = self.check_logs()
            if not txt:
                txt, debugmsg = await self.speaking.process_input(last_message_content)
                if not txt:  # emoji fallback if none
                    txt = self.emojihandler.emojihandler(picked_channel)
        else:
            txt, debugmsg = await self.speaking.process_input(last_message_content)
            if not txt:  # emoji fallback if none
                txt = self.emojihandler.emojihandler(picked_channel)
        await channel.send(txt)

    async def reaction(self, picked_channel, last_message):
        # adds reaction to last message, skip if already reacted
        x = last_message.reactions
        wasme = False
        for i in x:
            if i.me:
                wasme = True
        if not wasme:
            picked_emoji = self.emojihandler.emojihandler(picked_channel)
            await last_message.add_reaction(picked_emoji)
        else:
            if debug_on():
                log(f'[Reflex] - Already reacted to this message')

    async def reply(self, picked_channel, last_message):
        if not last_message:
            log(f'[Reflex] - No proper messages to use, emoji fallback')
            picked_emoji = self.emojihandler.emojihandler(picked_channel)
            await last_message.reply(picked_emoji)
            return
        # replies on last message sent in selected channel
        last_message_content = last_message.content
        if random.uniform(0.0, 1.0) < 0.25:
            txt = self.check_logs()
            if not txt:
                txt, debugmsg = await self.speaking.process_input(last_message_content)
                if not txt:  # emoji fallback if none
                    txt = self.emojihandler.emojihandler(picked_channel)
        else:
            txt, debugmsg = await self.speaking.process_input(last_message_content)
            if not txt:  # emoji fallback if none
                txt = self.emojihandler.emojihandler(picked_channel)
        await last_message.reply(txt)

    async def gif(self, picked_channel):
        channel = self.client.get_channel(picked_channel)
        gif = self.gif_finder.find("")
        if gif:
            await channel.send(gif)

    async def url(self, picked_channel):
        channel = self.client.get_channel(picked_channel)
        url = await self.urlhandler.get_url(channel, None)
        await channel.send(url)
