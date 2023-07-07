# i dont quite remember why i wrote this lul
import asyncio

class Serverdata:
    def getGuilds(self):
        guild_list = []
        for guild in self.guilds:
            guild_list.append(guild)
        return guild_list #return list of all guilds woodhouse is in.

    def getChannels(self, GuildId):
        y = self.get_guild(GuildId)
        x = y.get_member(795675666401198101)
        channel_list = []
        for channel in self.get_guild(GuildId).text_channels:
            z = channel.permissions_for(x).send_messages
            if z == True:
                channel_list.append(channel)
        return channel_list #return a list of channels Woodhouse is allowed to speak in on this guild

    def getMembers(self, GuildId):
        member_list = []
        for member in self.get_guild(GuildId).members:
            if member.bot == False:
                member_list.append(member)
        return member_list #return a list of members in a guild thats not a bot.

    async def wasItMe(self, channel):
        async for message in channel.history(limit=1):
            if message.author == self.user:
                return True #return True if last message in provided channel was the bots.
            else:
                return False