# https://realpython.com/python-logging/
# https://realpython.com/python-requests/
import logging
# https://docs.python.org/3/library/argparse.html#nargs
# https://pymotw.com/3/argparse/
# https://docs.python.org/3/library/argparse.html
import argparse
import json
import urllib.parse
# https://requests.readthedocs.io/en/latest/user/quickstart/
import requests
import sys
import subprocess
from requests.exceptions import HTTPError



HOME = "https://subsplease.org/"

# API config
API_URL = urllib.parse.urljoin("https://subsplease.org/", "api/")
TIME_ZONE = {"tz" : "Europe/Paris"}

def fetch(url:str, payload:dict):
    try:
        response = requests.get(url, params=payload)
        response.raise_for_status()
    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logging.error(f'Other error occurred: {err}')
    else:
        logging.info('Update Successful!')

    return json.loads(response.text)

def fetch_schedule():
    payload = {"f" : "schedule", "h" : "true", **TIME_ZONE}
    return fetch(API_URL, payload)["schedule"]

def fetch_latest():
    payload = {"f" : "latest", **TIME_ZONE}
    return fetch(API_URL, payload)

# def print_latest():
#     latest = fetch_latest()
#     for key, value in latest.items():
#         time = f'[{value["time"]}]'.upper() if value["time"] == "New" else value["time"]

#         print(f'\"{value["show"]}\" Ep {value["episode"]} {value["release_date"]} {time}')
#         for dl in value["downloads"]:
#             print(f'\t{dl["res"]} - {dl["magnet"]}')
#         print()

def schedule():
    schedule = fetch_schedule()

    for item in schedule:
        checkmark = "[✔]" if item["aired"] else "[ ]"
        print(f'{checkmark} {item["time"]} {item["title"]}')


def download(show_name:str, resolution):
    latest = fetch_latest()
    # xdg-open
    show = None
    show_name_stripped = show_name.strip()
    for key, value in latest.items():
        if show_name_stripped.lower() in key.lower():
            show = value
            break

    if show is None:
        print(f"Not found: {show_name_stripped}", file=sys.stderr)
        return

    downloads = value["downloads"] if show else None
    s = [item for item in downloads if resolution[:-1] == item["res"]]
    f = s[0]
    link = urllib.parse.unquote(f["magnet"])
    result = subprocess.call(f"xdg-open \"{link}\"", shell=True)
    print(f"script returned: {result}", file=sys.stderr)


def default(all_shows:bool=None):
    if all_shows:
        shows = fetch_latest().values()
    else:
        shows = [show for show in fetch_latest().values() if show["time"] == "New"]

    col_width = max(len(show['show']) for show in shows)
    for value in shows:
        if all_shows:
            time = f'[{value["time"]}]'.upper() if value["time"] == "New" else value["time"]
        else:
            time = ""

        line = f'{value["show"]:<{col_width}}  {value["episode"]:<4}  {value["release_date"]} {time}'

        print(line)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--all", action="store_true", default=False, help="list only the new shows")
    parser.add_argument("-skd", "--schedule", action="store_true", help="list the show schedule for the day")

    download_choices = ["480p", "540p", "720p", "1080p", "xdcc"]
    group = parser.add_argument_group('download')
    group.add_argument("-d", "--download", type=str, action="store", help="download a show")
    group.add_argument("-r", "--resolution", type=str, action="store", choices=download_choices, default=download_choices[3], help="the resolution of the show") # add nargs='+' to support multiple resolution

    # TODO: list the available resolutions
    # TODO: -r on it's own should not work.

    args = parser.parse_args()

    if args.schedule:
        schedule()
    elif args.download and args.resolution:
        download(args.download, args.resolution)
    elif args.all:
        default(all_shows=True)
    else:
        default()
