# logger just import log method into file you work with and add a
# "[System] - " before your log message to easily tell what system the message comes from :)

import time
import discord
import re
import os
from sys import platform


# Debugging
# do more stuff for debugging (specially no writing or finalizing of tasks just printing
def debug_on():
    debug = True
    return debug


def get_timestamp():
    i = time.strftime("%H:%M:%S - ")
    return i


def remove_emoji(text):
    result = re.subn(r'<a?:\w+:\d+>', '', text)[0]
    return result


# create and append to file named for usr in server subdir in /log and log rotation for statistics?
def logtofile(server, message, author):
    server = server.lower().replace(" ", "")
    folderpath = f'./log/{server}'
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)
    filepath = f'{folderpath}/{author}'
    f = open(filepath, 'a', encoding='utf-8')
    # run through both cleaning function that needs revising
    # message = remove_emoji(message)
    message = cleanmessage(message)
    if message is None:
        f.close()
        return
    f.write(message + "\n")
    f.close()


# this and remove emoji needs to revised to include emojis for statistics stuff.
# this is the old pattern r'^(http|<?https?:\S+)|^\s|^\W|^\d+$|^\d|^\s*$'
# trying out this new one
def cleanmessage(message):
    no = re.search(r'^(https?://\S+)|^\s*|^\W|^\d+$', message)
    if no:
        if debug_on():
            log(f'[INFO][Logger] - [{message}] DENIED by cleanMessage')
        return None  # return none if message is flagged by regex
    return message


# Call log(string) to normal log all stuff
# also added platform checks cause developing on Windows is helpful with timestamps
# n linux systemd does it for you.
def log(message, flag="[LOG] "):
    if not isinstance(message, discord.Message):
        if platform == "win32":
            x = get_timestamp()
            msg = flag.upper() + x + str(message)
        else:
            msg = flag.upper() + str(message)
        print(msg)
        return

    if message.channel.type == discord.ChannelType.private:
        if platform == "win32":
            x = get_timestamp()
            msg = f'[MSG] {x}[{message.channel}] - {message.author} : {message.content}'
            print(msg)
        else:
            msg = f'[MSG] [{message.channel}] - {message.author} : {message.content}'
            print(msg)

    else:
        if platform == "win32":
            x = get_timestamp()
            msg = f'[MSG] {x}[{message.channel.guild}] [{message.channel}] - {message.author} : {message.content}'
            print(msg)
        else:
            msg = f'[MSG] [{message.channel.guild}][{message.channel}] - {message.author} : {message.content}'
            print(msg)
        if message.author.bot:
            return
        logtofile(str(message.channel.guild), str(message.content), str(message.author))
