from systems.logger import log
from systems.varmanager import VarManager
import json
from collections import Counter


class Fishstats:
    def __init__(self):
        self.varmanager = VarManager()
        self.fishdata = None
        self.fishwrdata = None

    async def command(self, message):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            if message.channel.id in fishing_channels:
                # re-read stats files on command
                self.load_stats_files()

                # collect stuff
                totals_list = self.get_totals()
                biggest, mostwrs = self.get_wr_stuff()
                stats_msg = f'---- Fishing Simulator Statistics ----\n'
                stats_msg += f'Total fish caught {totals_list[1]}({totals_list[0]})\n'
                stats_msg += f'Total failed casts {totals_list[3]}({totals_list[2]})\n'
                stats_msg += f'Total shinies caught {totals_list[5]}({totals_list[4]})\n'
                stats_msg += f'Total uniques caught {totals_list[7]}({totals_list[6]})\n'
                stats_msg += f'Most caught fish {totals_list[8]}\n'
                stats_msg += f'Least caught fish {totals_list[9]}\n'
                stats_msg += f'Most shiny fish {totals_list[10]}\n'
                stats_msg += f'{biggest}\n'
                stats_msg += f'{mostwrs}\n'

                await message.channel.send(f'```yaml\n\n{stats_msg}```')

    def load_stats_files(self):
        with open(f"./local/fishing/stats.json", "r") as f:
            self.fishdata = json.load(f)

        with open(f"./local/fishing/wr.json", "r") as f:
            self.fishwrdata = json.load(f)

    def get_totals(self):
        # totals as INT
        total_caught_all = self.fishdata["alltime"]["catches"]
        total_caught_mon = self.fishdata["month"]["catches"]
        total_fail_all = self.fishdata["alltime"]["fails"]
        total_fail_mon = self.fishdata["month"]["fails"]
        total_shinies_all = self.fishdata["alltime"]["shinies"]
        total_shinies_mon = self.fishdata["month"]["shinies"]
        total_uniques_all = self.fishdata["alltime"]["uniques"]
        total_uniques_mon = self.fishdata["month"]["uniques"]

        # STR
        max_catches = max(self.fishdata["fish"].items(), key=lambda x: x[1]["catches"])
        max_catches_fish = f'{max_catches[0]} ({max_catches[1]["catches"]})'

        min_catches = min(self.fishdata["fish"].items(), key=lambda x: x[1]["catches"])
        min_catches_fish = f'{min_catches[0]} ({min_catches[1]["catches"]})'

        max_shiny = max(self.fishdata["fish"].items(), key=lambda x: x[1]["shinies"])
        max_shiny_fish = f'{max_shiny[0]} ({max_shiny[1]["shinies"]})'

        return (total_caught_all, total_caught_mon, total_fail_all, total_fail_mon, total_shinies_all, total_shinies_mon,
                total_uniques_all, total_uniques_mon, max_catches_fish, min_catches_fish, max_shiny_fish)


    def get_wr_stuff(self):
        # get biggest fish
        biggest_wr = max(self.fishwrdata.items(), key=lambda x: x[1]["weight"])
        biggest_ever_fish = f'Largest fish ever caught {biggest_wr[0]} at {biggest_wr[1]["weight"]} lbs by {biggest_wr[1]["holder"]}'

        # get most wrs
        record_holders = [info["holder"] for info in self.fishwrdata.values()]
        record_holder_counts = Counter(record_holders)
        most_common_holder = record_holder_counts.most_common(1)
        holder, count = most_common_holder[0]
        most_wrs = f'{holder} holds most world records at {count}'

        return biggest_ever_fish, most_wrs




#    msg = f'''---- Fishing Simulator Statistics ----
#Most active fisher : {activeUser} {activeCatches} catch(es)
#Least active fisher : {LactiveUser} {LactiveCatches} catch(es)
#Unluckiest fisher : {unluckyUser} {mostFails} fails
#Most diverse fisher : {longestBucket} {longestNumb} types in bucket
#Most caught shinies : {shinyUser} ({shinyCatches})
#Most world records : {mostWRs}
#Top total weight in bucket : {totalWeightUser} {totalWeightUserWeight} lbs
#Biggest fish ever caught : {biggestFishNa} at {biggestFishWe} lbs
