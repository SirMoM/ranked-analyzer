import argparse
import json
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any

from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.dates import DateFormatter

from models import GameData, GameDecoder
from utils.LOG import get_logger

FORMAT_H_M = "%H:%M"

LOG = get_logger("R")


@dataclass
class ScriptOptions:
    puuid: str
    filename: str
    input_file: str


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Script for rendering the game data collected by "
        "game_data_collector.py"
    )
    parser.add_argument(
        "-p",
        "--puuid",
        required=True,
        type=str,
        help="Unique identifier for the player",
    )
    parser.add_argument(
        "-if",
        "--input_filename",
        required=True,
        type=str,
        help="Input filename",
    )
    parser.add_argument(
        "-f",
        "--filename",
        required=False,
        type=str,
        help="Filename for the resulting image",
        default="plot.png",
    )

    _opts = parser.parse_args()

    return ScriptOptions(_opts.puuid, _opts.filename, _opts.input_filename)


class QueueType(Enum):
    FLEX = 440
    OTHER = -1

    def __str__(self) -> string:
        return self.name

    def __repr__(self):
        return f"{self.name} {self.value}"


@dataclass
class GameRenderData:
    started: datetime
    won: bool
    q_type: QueueType

    def __init__(self, _started: datetime, _won: bool, _q_type: QueueType):
        self.started = _started
        self.won = _won
        self.q_type = _q_type

    @classmethod
    def from_game_data(cls, game_data: GameData, _puuid: string) -> "GameRenderData":
        start_time = datetime.utcfromtimestamp(game_data.info.gameStartTimestamp / 1000)
        q_type = (
            QueueType.FLEX
            if game_data.info.queueId == QueueType.FLEX.value
            else QueueType.OTHER
        )

        uuid_idx = game_data.metadata.participants.index(_puuid)
        team_idx = 1 if uuid_idx >= 5 else 0
        did_win = game_data.info.teams[team_idx].win

        return GameRenderData(_started=start_time, _won=did_win, _q_type=q_type)


def round_to_quarter_hour(_time):
    minutes = 0
    if _time.minute > 45:
        minutes = 45
    elif _time.minute > 30:
        minutes = 30
    elif _time.minute > 15:
        minutes = 15

    return _time.replace(
        year=1970, month=1, day=1, second=0, microsecond=0, minute=int(minutes)
    )


def load_game_data(filename: string) -> list[GameData]:
    with open(filename, "r") as file:
        return json.load(file, cls=GameDecoder)


def win_rate_to_color(win_rate: float, ignore_value: int):
    # Ensure win_rate is within range [0.0, 1.0]
    win_rate = max(0.0, min(1.0, win_rate))

    red_green_colors = [(0.9, 0, 0, 0.9), (0, 0.7, 0, 0.9)]  # Red to green
    red_green_cmap = LinearSegmentedColormap.from_list("RedGreen", red_green_colors)

    color = red_green_cmap(win_rate)
    if ignore_value == 0:
        return 0, 0, 0, 0
    return color


def autolabel(rects, text: List[str]):
    """
    Attach a text label above each bar displaying its height
    """
    for _idx, rect in enumerate(rects):
        height = rect.get_height()
        txt = text[_idx]
        if txt != "0/0":
            pos = rect.get_x() + rect.get_width() / 2.0, 1
            plt.text(*pos, f"{txt}", ha="center", va="bottom", rotation=-90)


if __name__ == "__main__":
    opts: ScriptOptions = parse_arguments()

    class RenderPoint:
        timestamp: datetime
        won_games: int = 0
        total_games: int = 0
        win_rate: float = 0.0

        def __init__(self, time: datetime):
            self.timestamp = time

        def add_game_result(self, game_won: bool) -> "RenderPoint":
            self.total_games += 1
            self.won_games += 1 if game_won else 0
            self.win_rate = (
                self.won_games / self.total_games  # if self.won_games > 0 else 0
            )
            return self

    timeslots: Dict[str, RenderPoint] = {}

    # Prefill timeslots with 0
    start = datetime.fromisoformat("1970-01-01 00:00:00")
    for step in range(0, 24 * 4, 1):
        start = start + timedelta(minutes=15)
        key = start.strftime("%H:%M")
        _rp = RenderPoint(start)
        _rp.total_games = 0
        timeslots[key] = _rp

    games: List[GameData] = load_game_data(opts.input_file)

    game_render_data: List[GameRenderData] = [
        GameRenderData.from_game_data(game, opts.puuid) for game in games
    ]
    LOG.info("Loaded game data")

    LOG.debug("Extracting render data")

    # Only use FLEX_Q games
    game_render_data = [
        game for game in game_render_data if game.q_type == QueueType.FLEX
    ]

    for game in game_render_data:
        time = round_to_quarter_hour(game.started)
        key = time.strftime(FORMAT_H_M)
        _rp = timeslots[key]
        if _rp is None:
            timeslots[key] = RenderPoint(time).add_game_result(game.won)
        else:
            timeslots[key] = timeslots[key].add_game_result(game.won)
    LOG.debug("Extracted map of timeslots and winrates!")

    rp: List[RenderPoint] = [v for v in timeslots.values()]

    # sort by timestamps
    sorted_rp: List[RenderPoint] = sorted(rp, key=lambda x: x.timestamp)

    x_ts = [rp.timestamp for rp in sorted_rp]
    y_wr = [rp.win_rate * 100 for rp in sorted_rp]
    c = [win_rate_to_color(_rp.win_rate, _rp.total_games) for _rp in sorted_rp]
    text = [f"{_rp.won_games}/{_rp.total_games}" for _rp in sorted_rp]
    LOG.debug("Finished creating render points, color and data!")

    # Trim unused / empty timeslots for the graph
    for idx, _ in enumerate(rp):
        if rp[idx].total_games > 0:
            x_ts = x_ts[idx - 2 :]
            y_wr = y_wr[idx - 2 :]
            c = c[idx - 2 :]
            text = text[idx - 2 :]
            break
    LOG.debug("Trimed empty time slots")

    LOG.info("Started graph creation")
    plt.figure(figsize=(21.69, 8.27))
    plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M"))
    bar = plt.bar(
        x_ts,
        height=y_wr,
        color=c,
        align="center",
        width=timedelta(minutes=15),
    )

    # Adds the text into the bars
    autolabel(bar, text)

    plt.xlabel("Time [HH:mm] ")
    plt.ylabel("Win Rate [%]")
    plt.title(
        f"Win Rate Over Time (15-minute Time Boxes) for {len(game_render_data)} games"
    )
    plt.grid(True)

    # Tick every 30 minutes
    plt.xticks(
        [v for idx, v in enumerate(x_ts) if (idx + 1) % 2 == 0],
        rotation=-90,
        fontsize=9,
    )

    plt.savefig(opts.filename)
    plt.show()
    LOG.info(f"Save plot to file '{opts.filename}'")
