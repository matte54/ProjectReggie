import json


class Reminder_handler():
    def __init__(self, client):
        self.client = client

    async def track_reminders(self):
        await self.client.wait_until_ready()
        #while True:
        #    pass