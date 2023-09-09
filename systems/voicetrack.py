# this is put on hold for now

import os
import json
import datetime

from systems.logger import log


class Voicetrack:
    def __init__(self):
        self.user_in_voice = False
        self.user_id = None

        self.user_join_time = None
        self.user_leave_time = None

    async def process(self, member, voice_before, voice_after):
        self.user_id = member.id
        if voice_before.channel != voice_after.channel:  # check for voice state change
            if self.user_in_voice and voice_after.channel is not None:
                # user switched from one voice channel to another
                pass

            if voice_after.channel is None:
                # user left voice completely
                pass

            if voice_before.channel is None:
                # user joined a voice channel
                self.user_in_voice = True
                self.user_join_time = datetime.datetime.now()

    def calculate_time_spent(self):
        pass
