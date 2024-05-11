import json
from dataclasses import dataclass
from typing import List, Dict, Any

from utils.LOG import get_logger


@dataclass
class GameMetadata:
    dataVersion: str
    matchId: str
    participants: List[str]


@dataclass
class Team:
    bans: list
    objectives: Dict[str, Dict[str, bool]]
    teamId: int
    win: bool


@dataclass
class GameInfo:
    endOfGameResult: str
    gameCreation: int
    gameDuration: int
    gameEndTimestamp: int
    gameId: int
    gameMode: str
    gameName: str
    gameStartTimestamp: int
    gameType: str
    gameVersion: str
    mapId: int
    platformId: str
    queueId: int
    teams: List[Team]
    tournamentCode: str
    participants: Any


@dataclass
class GameData:
    metadata: GameMetadata
    info: GameInfo


class GameDecoder(json.JSONDecoder):
    LOG = get_logger(__name__)

    def decode(self, s: str, **kwargs: Any) -> list[GameData]:
        data = super().decode(s, **kwargs)
        return [self._decode_data(_datum, idx) for idx, _datum in enumerate(data)]

    def _decode_data(self, data: Dict[str, Any], idx: int) -> Any:
        metadata, info, teams = "metadata", "info", "teams"
        try:
            if metadata in data:
                data[metadata] = GameMetadata(**data[metadata])
            if info in data:
                if teams in data[info]:
                    data[info][teams] = [Team(**team) for team in data[info][teams]]
                    if "endOfGameResult" in data[info]:
                        data[info] = GameInfo(**data[info])
                    else:
                        data[info] = GameInfo("", **data[info])

            return GameData(**data)
        except Exception as ex:
            self.LOG.warn(f"Json at index: [{idx}] threw exception {type(ex)}")
            self.LOG.error(ex)
            raise ex
