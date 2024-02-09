from dataclasses import dataclass
from typing import List


@dataclass
class DBRace:
    name: str
    scoring_modifier: float
    year: int

    def __init__(self):
        self.scoring_modifier = 1


@dataclass
class DBRaceResult:
    position: int | str
    pole: bool
    fastest_lap: bool
    sprint_result: int | None
    points: int

    def __init__(self):
        self.pole = False
        self.fastest_lap = False
        self.sprint_result = None
        self.points = 0


@dataclass
class DBDriver:
    name: str
    year: int
    races: List[DBRaceResult | None]
    total_points: int
    championship_position: int | None

    def __init__(self):
        self.races = []
        self.total_points = 0
        self.championship_position = None


@dataclass
class DBPointsPeriod:
    start: int
    end: int | None
    points_distribution: dict
    fastest_lap_always: bool

    def __init__(self):
        self.end = None
        self.points_distribution = {}
        self.fastest_lap_always = False
