import discord
import os
import platform
import requests
import socket

from systems.logger import log

class Whoami:
    def __init__(self, client):
        self.client = client

    async def command(self, message):
        log(f'[Whoami] - {message.author} About woodhouse')
        url = "http://checkip.dyndns.org"
        request = requests.get(url)
        clean = request.text.split(': ', 1)[1]
        my_ip = clean.split('</body></html>', 1)[0]
        my_host = socket.gethostname()

        # LUL
        s = f'Hello i am {self.client.user.name} a bot by matte54'
        y = f"Discord.py API version: {discord.__version__}"
        z = f"Python version: {platform.python_version()}"
        o = f"Running on: {platform.system()} {platform.release()} ({os.name.upper()})"
        l = f'{my_host} - {my_ip}'
        u = f'source: https://github.com/matte54/ProjectReggie'
        final_output = "\n".join([s, y, z, o, l, u])
        x = f'```yaml\n\n{final_output}```'

        await message.channel.send(x)
