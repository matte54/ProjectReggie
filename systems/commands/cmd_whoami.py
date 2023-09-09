import discord
import os
import datetime
import requests
import socket
import platform

from systems.logger import log


class Whoami:
    def __init__(self, client):
        self.client = client
        self.dyndns_url = "http://checkip.dyndns.org"
        self.gathering = None

    async def command(self, message):
        self.gathering = False
        log(f'[Whoami] - {message.author} About woodhouse')
        msg = await message.channel.send("Gathering data... (this command can sometimes take time)")
        ip, host = await self.gather_info()
        x = await self.create_string(ip, host)

        await msg.edit(content=x)


    async def create_string(self, my_ip, my_host):
        greet = f'Hello i am {self.client.user.name} a bot by matte54'
        discordpy_v = f"Discord.py API version: {discord.__version__}"
        python_v = f"Python version: {platform.python_version()}"
        platform_info = f"Running on: {platform.system()} {platform.release()} ({os.name.upper()})"
        host_info = f'{my_host} - {my_ip}'
        source_info = f'source: https://github.com/matte54/ProjectReggie'
        now = datetime.datetime.now()
        localtime_info = f'localtime: {now.strftime("%Y-%m-%d %H:%M:%S")}'
        final_output = "\n".join([greet, discordpy_v, python_v, platform_info, host_info, source_info, localtime_info])
        return f'```yaml\n\n{final_output}```'


    async def gather_info(self):
        self.gathering = True
        request = requests.get(self.dyndns_url, timeout=10)
        if request.status_code == 200:
            clean = request.text.split(': ', 1)[1]
            my_ip = clean.split('</body></html>', 1)[0]
        else:
            my_ip = "unable to retrive ip"
        my_host = socket.gethostname()


        return my_ip, my_host
