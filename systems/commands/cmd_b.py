import os
import re
from systems.logger import log
from systems.banditlife import banditlife


class B:
    def __init__(self, client):
        self.client = client
        self.msg_obj = None
        self.user_id = None
        self.input_str = None
        self.banditlife = banditlife.Banditlife()
        self.cmdlist = {
            "respawn": self.respawn,
            "raid": self.raid,
            "suicide": self.suicide
        }

        # paths
        self.profile_dir = "./local/banditlife/profiles/"

    async def command(self, message):
        self.msg_obj = message
        self.user_id = message.author.id
        content = message.content.replace('$', '').lower()
        words = content.split()

        if len(words) < 2:
            # make sure there is a subcmd
            await self.msg_obj.channel.send(f'```yaml\n\nThis command always needs a subcommand```')
            return

        remaining_words = words[2:]
        self.input_str = ' '.join(remaining_words)

        command_function = self.cmdlist.get(words[1])

        if command_function:
            await command_function()

        else:
            log(f'[Banditlife] - "{words[1]}" is not a valid subcommand')
            await self.msg_obj.channel.send(f'```yaml\n\nInvalid subcommand```')

    async def respawn(self):
        if os.path.exists(f'{self.profile_dir}{self.user_id}.json'):
            await self.msg_obj.channel.send(f'```yaml\n\nYou already have a profile```')
            return
            # make players able to suicide and delete their profile
        else:
            words = self.input_str.split(" ")
            if len(words) == 0 or len(words) > 1:
                await self.msg_obj.channel.send(f'```yaml\n\nNo spaces```')
                return
            name = words[0]
            # check naming rules
            if 3 <= len(name) <= 24:
                if re.match(r'^[a-zA-Z]+$', name):
                    self.banditlife.create_profile(self.user_id, name)
                    await self.msg_obj.add_reaction("👍")
                else:
                    await self.msg_obj.channel.send(f'```yaml\n\nOnly english ascii characters allowed```')
            else:
                await self.msg_obj.channel.send(f'```yaml\n\nName needs to be between 3-24 characters```')

    async def suicide(self):
        if os.path.exists(f'{self.profile_dir}{self.user_id}.json'):
            os.remove(f'{self.profile_dir}{self.user_id}.json')
            await self.msg_obj.add_reaction("👍")
            log(f'[Banditlife] - Suicide...deleting {self.profile_dir}{self.user_id}.json')

    async def raid(self):
        print("raid")
