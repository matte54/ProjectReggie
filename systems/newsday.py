from systems.logger import log
import os
import re


class Newsday:
    def __init__(self, client):
        self.client = client
        self.livechannels = [327131365944590337]

    def newsdaylog(self, message):
        if message.channel.id in self.livechannels:
            no = re.search(r'^(https?://\S+)|^\W|^\d+$', message.content)
            if not no:
                server = str(message.channel.guild).lower().replace(" ", "")
                folderpath = f'./log/{server}'
                if not os.path.exists(folderpath):
                    os.makedirs(folderpath)
                filepath = f'{folderpath}/newsday{str(message.channel.id)}.log'

                with open(filepath, "r", encoding='utf-8') as f:
                    character_count = sum(len(line) for line in f)
                    print(character_count)
                if (character_count + len(message.content)) >= 4000:
                    print("File is 4000 characters")



                with open(filepath, "a", encoding='utf-8') as f:
                    f.write(f'{message.author} - {message.content}\n')
