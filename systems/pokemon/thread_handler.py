import discord
import asyncio

from systems.varmanager import VarManager
from systems.logger import debug_on, log


class Threader:
    def __init__(self, client):
        self.pokemon_channels = []
        self.userthreads = {}
        self.client = client
        self.varmanager = VarManager()

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

    async def handle_thread(self, message, name, content, first_msg=None):
        user_id = message.author.id

        # Check if the user already has a thread
        if user_id in self.userthreads:
            try:
                # Fetch the existing thread using the stored thread ID
                thread = await self.client.fetch_channel(self.userthreads[user_id])

                # If the thread's name matches the user's name, reuse it
                if thread.name == name and not thread.archived:
                    if isinstance(content, list):
                        await thread.send(files=content)
                    else:
                        await thread.send(content)
                    return thread
                else:
                    # If the thread is not valid (archived or the name doesn't match), delete it and create a new one
                    await thread.delete()
                    del self.userthreads[user_id]
                    log(f'[Pokemon] - Deleted old thread for {name}, user_id: {user_id}')

            except (discord.NotFound, discord.Forbidden):
                # If the thread is not found or is inaccessible, we proceed to create a new thread
                log(f'[Pokemon] - Thread not found or inaccessible for {name}, user_id: {user_id}')
                pass

        # If no valid thread was found or we deleted the old one, create a new one
        try:
            # Fetch the original message (in case it's needed)
            message = await message.channel.fetch_message(message.id)

            # Create a new thread with the user's name
            thread = await message.create_thread(name=name, auto_archive_duration=60)
            self.userthreads[user_id] = thread.id  # Store the new thread ID

            # Send the initial message
            if first_msg:
                await thread.send(f'{first_msg} {message.author.mention}')
            if isinstance(content, list):
                await thread.send(files=content)
            else:
                await thread.send(content)

            log(f'[Pokemon] - Created new thread for {name}, thread_id: {thread.id}')

            return thread

        except discord.Forbidden:
            log(f'[Pokemon]- error, no permission to create threads')
            return None
        except discord.HTTPException as e:
            log(f'[Pokemon]- Failed to create thread: {e}')
            return None

    async def send_msg(self, channel_id, msg):
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            ch = self.client.get_channel(channel_id)

            if ch is None:
                log(f'[Pokemon]- Channel {channel_id} not found. Retrying in {delay * (2 ** attempt)}s...')
            else:
                try:
                    x = await ch.send(msg)
                    break  # Successfully sent, exit retry loop
                except (discord.HTTPException, discord.Forbidden, discord.NotFound) as e:
                    log(f'[Pokemon]- Error sending message (attempt {attempt + 1}/{max_retries}): {e}')

            await asyncio.sleep(delay * (2 ** attempt))

        else:  # This else runs only if all retries fail
            log(f'[Pokemon]- Failed to send message to {channel_id} after {max_retries} retries.')

    async def send_to_all(self, msg):
        max_retries = 3
        delay = 2
        messages = []

        for channel_id in self.pokemon_channels:
            for attempt in range(max_retries):
                ch = self.client.get_channel(channel_id)

                if ch is None:
                    log(f'[Pokemon]- Channel {channel_id} not found. Retrying in {delay * (2 ** attempt)}s...')
                else:
                    try:
                        x = await ch.send(msg)
                        messages.append(x)
                        break  # Successfully sent, exit retry loop
                    except (discord.HTTPException, discord.Forbidden, discord.NotFound) as e:
                        log(f'[Pokemon]- Error sending message (attempt {attempt + 1}/{max_retries}): {e}')

                await asyncio.sleep(delay * (2 ** attempt))

            else:  # This else runs only if all retries fail
                log(f'[Pokemon]- Failed to send message to {channel_id} after {max_retries} retries.')

        return messages
