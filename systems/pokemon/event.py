import asyncio
import json

from systems.pokemon.set_data import x as set_data
from systems.varmanager import VarManager
from systems.logger import debug_on, log


class Eventmanager:
    def __init__(self):
        self.varmanager = VarManager()
        self.setdatalist = set_data
        self.set_ids = {t[0] for t in self.setdatalist}

    async def start_event(self, set_id):
        if set_id not in self.set_ids:
            return None

        with open(f'./data/pokemon/setdata/{set_id}_setdata.json', "r") as f:
            event_data = json.load(f)

        self.varmanager.write("pokemon_event", set_id)
        log(f'[Pokemon] - starting event for set {set_id}')
        return event_data

    async def stop_event(self):
        self.varmanager.write("pokemon_event", "")
        log(f'[Pokemon] - stopping event')



