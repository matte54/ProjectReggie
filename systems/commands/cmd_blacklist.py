# ugly little blacklist command to use in other function for an admin to add channel ids that woodhouse
# shouldnt mess do stuff in.

from systems.varmanager import VarManager
from systems.logger import log, debug_on
from data.etc.admins import ADMINS


class Blacklist:
    def __init__(self):
        self.varmanager = VarManager()
        self.admins = ADMINS

    async def command(self, message):
        if message.author.id in self.admins:
            wordlist = message.content.split(" ", 3)
            try:
                if wordlist[1] == "add":
                    channelid = wordlist[2][2:][:-1]
                    if len(channelid) > 17:
                        if self.varmanager.read("black_channels"):
                            x = self.varmanager.read("black_channels")
                            if channelid not in x:
                                log(f'[Blacklist] - blacklisting {channelid}')
                                await message.add_reaction("👍")
                                x.append(channelid)
                                self.varmanager.write("black_channels", x)
                            else:
                                log(f'[Blacklist] - {channelid} already blacklisted')
                        else:
                            self.varmanager.write("black_channels", [channelid])  # if var dosent exist on file add new
                            log(f'[Blacklist] - blacklisting {channelid}')
                            await message.add_reaction("👍")
                    else:
                        log(f'[Blacklist] - {channelid} is not a valid channelid')

                elif wordlist[1] == "rm":
                    channelid = wordlist[2][2:][:-1]
                    if len(channelid) > 17:
                        try:
                            x = self.varmanager.read("black_channels")
                            if channelid in x:
                                x.remove(channelid)
                                self.varmanager.write("black_channels", x)
                                await message.add_reaction("👍")
                                log(f'[Blacklist] - Removing {channelid} from blacklist')
                            else:
                                log(f'[Blacklist] - {channelid} is not blacklisted')
                        except ValueError:
                            log(f'[Blacklist] - No channels blacklisted, nothing to remove')
                    else:
                        log(f'[Blacklist] - {channelid} is not a valid channelid')

                else:
                    print("Not a valid command")
            except IndexError:
                print("Error wrong command syntax")

        else:
            print("This is an admin only command")
