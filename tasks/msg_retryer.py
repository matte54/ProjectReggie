import asyncio
import discord

from systems.logger import log


class Msgretry:
    _instance = None

    def __new__(cls, client):
        if cls._instance is None:
            cls._instance = super(Msgretry, cls).__new__(cls)
            cls._instance.client = client
            cls._instance.run = True
            cls._instance.messages_to_retry = {}  # Shared storage
        return cls._instance  # Return the single instance

    async def store_msg(self, msg, channel_id):
        channel_id = str(channel_id)  # Convert channel_id to str for dictionary key
        if channel_id not in self.messages_to_retry:
            self.messages_to_retry[channel_id] = []
        self.messages_to_retry[channel_id].append(msg)

    async def msg_sender(self, msg, channel_id):
        max_retries = 3
        delay = 2
        channel_id = int(channel_id)  # Convert back to int

        ch = self.client.get_channel(channel_id)
        if ch is None:
            log(f'[Msg retryer] - Channel {channel_id} not found. Skipping message.')
            return  # Don't retry if channel is invalid

        for attempt in range(max_retries):
            try:
                await ch.send(msg)
                return  # Successfully sent, exit function
            except (discord.HTTPException, discord.Forbidden, discord.NotFound) as e:
                log(f'[Msg retryer] - Error sending message (attempt {attempt + 1}/{max_retries}): {e}')
                await asyncio.sleep(delay * (2 ** attempt))

        log(f'[Msg retryer] - Failed to send message to {channel_id} after {max_retries} retries.')

    async def main(self):
        await asyncio.sleep(10)
        log(f'[Msg retryer] - Initializing')

        while self.run:
            if self.messages_to_retry:
                for channel_id in list(self.messages_to_retry.keys()):  # Iterate safely
                    for msg in self.messages_to_retry[channel_id]:
                        await self.msg_sender(msg, channel_id)

                    # Remove channel entry after sending all messages
                    del self.messages_to_retry[channel_id]

            await asyncio.sleep(360)
