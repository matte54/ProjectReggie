import asyncio
from datetime import datetime

from systems.logger import log


class Pokemoneventhandler:
    def __init__(self, client):
        self.client = client
        self.last_friday_run = None
        self.last_saturday_run = None

    async def friday_task(self):
        log(f'[Pokemon][Event Handler] - Starting event')

    async def saturday_task(self):
        log(f'[Pokemon][Event Handler] - Stopping event')

    async def main(self):
        await asyncio.sleep(10)
        log(f'[Pokemon][Event Handler] - Initilizing')
        while True:
            now = datetime.now()

            # Check for 3 PM on Friday
            if now.weekday() == 4 and now.hour == 15 and self.last_friday_run != now.date():
                await self.friday_task()
                self.last_friday_run = now.date()

            # Check for 8 PM on Saturday
            if now.weekday() == 5 and now.hour == 20 and self.last_saturday_run != now.date():
                await self.saturday_task()
                self.last_saturday_run = now.date()

            await asyncio.sleep(60)
