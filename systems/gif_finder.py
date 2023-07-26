# returns a random gif url from giphy based on query
# if query is blank you get a random trending one.
# if key is missing or there is some sort of problem it returns None

import requests
import os
import random
from systems.logger import log, debug_on

# make sure key file exist
if os.path.isfile("./data/etc/giphy_key.py"):
    from data.etc.giphy_key import KEY
    found_key = True
else:
    found_key = False


class Giphy_find:
    def __init__(self):
        self.limit = 5

    def find(self, query):
        if found_key:
            if not query:
                # if query string is blank get trending
                url = "https://api.giphy.com/v1/gifs/trending"
                params = {"api_key": KEY,
                          "limit": self.limit}
            else:
                # search gifs based no query string
                url = "https://api.giphy.com/v1/gifs/search"
                params = {"api_key": KEY,
                          "q": query,
                          "limit": self.limit}
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()  # Check for errors in the response

                data = response.json()
                gifs = data["data"]

                # Extract the GIF URLs from the response
                gif_urls = [gif["images"]["fixed_height"]["url"] for gif in gifs]
                chosen_gif = random.choice(gif_urls)
                return chosen_gif

            except requests.exceptions.RequestException as e:
                print("Error occurred:", e)
                return None
        else:
            log(f'[Giphy] - Error no api key found')
            return None

