import argparse
import os
import string
from dataclasses import dataclass
from datetime import datetime
from typing import List

import requests
from dotenv import load_dotenv

from utils.waiting_strategy import *
from utils.LOG import get_logger, stringify
from utils.progessbar import print_progress

LOG = get_logger("GDC")
BASE_URL = "https://europe.api.riotgames.com"


@dataclass
class ScriptOptions:
    game_name: str
    tag: str
    filename: str
    amount: int


def get_puuid_for_game_name_tag(game_name: string, tag: string) -> string:
    response = requests.get(
        f"{BASE_URL}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}?api_key={API_KEY}"
    )
    return response.json()["puuid"]


def get_match_IDs(puuid: string, amount: int, start: int = 0):
    response = requests.get(
        f"{BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={amount}&api_key={API_KEY}"
    )
    if response.status_code != 200:
        LOG.error(response.json())
        raise Exception(response.json())
    else:
        return response.json()


def get_match_stats(
    match_id: string,
    waiting_strategy: WaitingStrategy = FibonacciStrategy(),
) -> string:
    url = f"{BASE_URL}/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    # url = "http://localhost:42069/"

    response = requests.get(url)
    response_body = response.json()

    if response.status_code == 200:
        waiting_strategy.decrease()
        return response_body
    elif response.status_code == 429:
        LOG.debug(
            f"Hit the request limit with status {response.status_code}: \n {response_body}\n"
        )
        waiting_strategy.wait()
        return get_match_stats(match_id, waiting_strategy)
    else:
        LOG.debug(response_body)
        raise Exception(
            f"[ERROR]: Request for {url} failed with: {response.status_code}\n{json.dumps(response_body, indent=2)}"
        )


def parse_arguments():
    parser = argparse.ArgumentParser(description="Description of your program")

    parser.add_argument(
        "-g", "--game_name", required=True, type=str, help="Name of the game"
    )
    parser.add_argument("-t", "--tag", required=True, type=str, help="Tag string")
    parser.add_argument("-a", "--amount", type=int, help="Amount as an integer")
    parser.add_argument("-f", "--filename", type=str, help="File name")

    _opts = parser.parse_args()

    return ScriptOptions(_opts.game_name, _opts.tag, _opts.filename, _opts.amount)


def fetch_match_ids(amount_of_matches_to_fetch: int) -> List[str]:
    LOG.debug(f"About to fetch {amount_of_matches_to_fetch} matches")
    _match_ids: List[str] = []
    if amount_of_matches_to_fetch > 100:
        fetched_matches = 0
        while amount_of_matches_to_fetch > 100:
            _match_ids.extend(
                get_match_IDs(puuid=puuid, amount=100, start=fetched_matches)
            )
            fetched_matches += 100
            amount_of_matches_to_fetch -= 100
            LOG.debug(
                f"FETCHED: {fetched_matches} of {fetched_matches + amount_of_matches_to_fetch}!"
            )
            print_progress(
                fetched_matches,
                fetched_matches + amount_of_matches_to_fetch,
                existing_bar=True,
            )
        _match_ids.extend(get_match_IDs(puuid=puuid, amount=amount_of_matches_to_fetch))
        print_progress(
            fetched_matches + amount_of_matches_to_fetch,
            fetched_matches + amount_of_matches_to_fetch,
            existing_bar=True,
        )
        print()
    else:
        _match_ids = get_match_IDs(puuid=puuid, amount=amount_of_matches_to_fetch)
    return _match_ids


def save_to_file(file_name: str, data):
    file_path = os.path.join("./data/", file_name + ".json")
    with open(file_path, "w") as file:
        json.dump(data, file)
    LOG.info(f"Dumped game stats for {opts.game_name}#{opts.tag} in {file_path}!")


def get_filename(_opts: ScriptOptions) -> str:
    current_date = datetime.now().strftime("%Y%m%d-%H%M%S")
    return (
        opts.filename
        if opts.filename is not None
        else f"{opts.game_name}#{opts.tag}+{current_date}"
    )


if __name__ == "__main__":
    # Load the API KEY from the .env file
    load_dotenv()
    API_KEY = os.environ.get("API_KEY")

    opts: ScriptOptions = parse_arguments()
    LOG.info(stringify(opts))

    puuid: string = get_puuid_for_game_name_tag(opts.game_name, opts.tag)
    LOG.info(f"Got PUUID: {puuid} for {opts.game_name}#{opts.tag}")

    amount_of_matches_to_fetch = opts.amount if opts.amount is not None else 100

    match_ids = fetch_match_ids(amount_of_matches_to_fetch)
    LOG.info(f"Fetched {len(match_ids)} match ids.")

    game_info_data: List = []

    try:
        for idx, match_id in enumerate(match_ids):
            LOG.debug(f"{idx}. fetching match: {match_id}")
            game_stats = get_match_stats(match_id)
            game_info_data.append(game_stats)

            print_progress(idx, len(match_ids), existing_bar=True)

    except Exception as e:
        print()
        LOG.error(f"Failed to fetch match", e)
    print()

    save_to_file(get_filename(opts), game_info_data)
    LOG.debug("-" * 80 + "\n\n")
