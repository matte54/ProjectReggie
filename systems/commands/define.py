import requests
from systems.logger import debug_on, log


# x = f'```yaml\n\n{final_output}```'

class Define:
    def __init__(self):
        self.freedict_json = None
        self.query = None
        self.freedict_response = None

    async def command(self, message):
        self.query = message.content.replace("$define ", "")

        # run free dictionary query
        freedict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{self.query}"
        try:
            self.freedict_response = requests.get(freedict_url)
        except requests.exceptions.RequestException:
            log(f'[Define] - Error occured reaching freedict api')

        if self.freedict_response:
            self.freedict_json = self.freedict_response.json()[0]
            # check if theres phoentics
            if self.freedict_json["phonetics"]:
                phonetics = self.freedict_json["phonetics"][0]["text"]
            else:
                phonetics = ""

            main_list = []
            # check all meanings
            meanings = self.freedict_json["meanings"]
            for section in meanings:
                # this is wordtype
                wordtypeList = []
                wordtypeList.append(section["partOfSpeech"].upper())
                for wordtype in section["definitions"]:
                    # all defintions for the wordtype
                    wordtypeList.append(wordtype["definition"])
                    if len(wordtypeList) > 3:
                        break
                main_list.append(wordtypeList)

            formatted_lists = '\n'.join(['\n'.join(f"{item:2}" for item in sublist) for sublist in main_list])

            freedict_yaml_response = f'```yaml\n\n' \
                                     f'{self.freedict_json["word"]} - {phonetics}\n' \
                                     f'{formatted_lists}' \
                                     f'```'
            await message.channel.send(freedict_yaml_response)
