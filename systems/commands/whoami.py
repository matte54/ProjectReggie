import discord
import os
import platform
import requests
import socket

# this system might need to be awaited or maybe just get exceptions for request timing out

class Whoami:
    def __init__(self, client):
        self.client = client
    def command(self):
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
        _ = "\n"
        k = s + _ + y + _ + z + _ + o + _ + l
        x = f'```yaml\n\n{k}```'
        return x
