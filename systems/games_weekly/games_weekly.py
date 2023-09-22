import requests
import json
import datetime
from bs4 import BeautifulSoup


def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def main():
    url = "https://www.gameinformer.com/this-week"

    response = requests.get(url)

    data = {}

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        game_elements = soup.find_all('div', class_='views-row')

        for game in game_elements:
            # Extract the title
            title_element = game.find('h3', class_='page-title')
            title = title_element.text.strip() if title_element else "N/A"

            # Extract the platform
            platform_element = game.find('div', class_='gi5-widget-platform')
            platform = platform_element.text.strip() if platform_element else "N/A"

            # Extract the release date
            release_date_element = game.find('div', class_='gi5-widget-release')
            release_date = release_date_element.text.strip() if release_date_element else "N/A"

            platform_string = platform.replace("Platform:\n", "")
            release_string = release_date.replace("Release:\n", "")
            data[title] = {}
            data[title]["platform"] = platform_string.replace("\n", ", ")
            data[title]["release"] = release_string.replace("\n", ", ")

        return data
    else:
        print("Failed to retrieve the web page. Status code:", response.status_code)
        return None


if __name__ == "__main__":
    videogames = main()

if videogames:
    today = datetime.datetime.now()
    week_number = today.strftime("%W")
    print(f'Scraped videogames for week {week_number}')
    write_json("./weeks_videogames.json", videogames)
