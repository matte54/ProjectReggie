import os
import re
import time
import difflib
from multiprocessing import Pool


from systems.logger import log

MATCH_LIMITER = 25000

# need to experiment with not using the avoid words? feel like i could get better results with it?

class Speaking:
    def __init__(self):
        self.data_path = "./data/redditdata/"
        self.avoidlist = []
        self.filter_pattern = r'[!()\[\]{};:\'"\\,<>./?@#$%^&*_~]'
        self.user_entry = None
        self.keywords = None
        self.debugstring = None

        # run this when intiating
        self.filter()

    def filter(self):
        path = "./data/etc/avoidwords.txt"
        with open(path, 'r', encoding='UTF-8') as f:
            text = f.read().splitlines()
        for word in text:
            self.avoidlist.append(word.lower())

    def data_generator(self):
        files = os.listdir(self.data_path)
        generatorloops = 0
        generator_matches = 0
        self.keywords = sorted(self.user_entry.split(), key=len, reverse=True)[:2]  # get longest words
        for file in files:
            with open(os.path.join(self.data_path, file), 'r', encoding='UTF-8') as f:
                for line in f:
                    generatorloops += 1
                    parts = line.strip().split(" / ")
                    if any(keyword in parts[0] for keyword in self.keywords):
                        generator_matches += 1
                        if generator_matches > MATCH_LIMITER:
                            break
                        yield tuple(parts)
        log(f'[Speaking] - Loops: {generatorloops}, Matches: {generator_matches}')
        self.debugstring += f'Loops: {generatorloops} Potencial Matches: {generator_matches}\n'

    def compare_entries(self, entry):
        if len(entry) >= 2:
            x = round(difflib.SequenceMatcher(a=self.user_entry, b=entry[0].lower()).ratio(), 2)
            return (entry[0], entry[1], x)
        else:
            return ("", "", 0.00)

    async def process_data(self):
        start_time = time.time()
        #best = ("", "", 0.00)
        #bestlist = []

        data = list(self.data_generator())  # Convert the generator to a list

        # Initialize a Pool of worker processes
        with Pool() as pool:
            # Use the pool to parallelize the comparison loop
            results = pool.map(self.compare_entries, data)

        # Find the best result from the parallel results
        best = max(results, key=lambda x: x[2])
        bestlist = [best]

        log(f'[Speaking] - Processing time was {round((time.time() - start_time))} second(s)')
        self.debugstring += f'Processing time: {round((time.time() - start_time))} second(s)\n'

        bestlist.sort(key=lambda y: y[2], reverse=True)

        if bestlist:
            rpicked = bestlist[0]  # trying just to pick the best and see how repetetive it gets...
            # rpicked = random.choice(bestlist[-5:])
            log(f'[Speaking] - {self.user_entry} <-{rpicked[2]}-> {rpicked[0]}')
            self.debugstring += f'{rpicked[2] * 100}% match: {rpicked[0]}\n\nOUTPUT: {rpicked[1]}'

            self.user_entry = None  # reset this variables after done
            self.keywords = None
            return rpicked[1], self.debugstring
        else:
            print("No matches!")
            self.user_entry = None  # reset this variables after done
            self.keywords = None
            return "Uhhh...no", None

    async def process_input(self, entry):
        self.debugstring = ""
        self.user_entry = entry.lower()
        self.user_entry = re.sub(self.filter_pattern, "", self.user_entry)  # remove ill-eagle characters
        self.user_entry = re.sub(r'^\s+', '', self.user_entry)
        self.debugstring += f'FILTERED INPUT: {self.user_entry}\n\n'
        # check list of ill-eagle words
        #for word in self.user_entry.split():
        #    if word in self.avoidlist:
        #        self.user_entry = self.user_entry.replace(word, "")

        return await self.process_data()
