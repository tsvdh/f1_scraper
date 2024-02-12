from dataclasses import dataclass
from typing import List

from pymongo import MongoClient


@dataclass
class DBRace:
    name: str
    scoring_modifier: float
    year: int
    flag_link: str
    index: int

    def __init__(self):
        self.scoring_modifier = 1

    def to_dict(self):
        return vars(self)


@dataclass
class DBRaceResult:
    position: int | str
    pole: bool
    fastest_lap: bool
    sprint_result: int | None
    points: int
    counts_for_total: bool

    def __init__(self):
        self.pole = False
        self.fastest_lap = False
        self.sprint_result = None
        self.points = 0
        self.counts_for_total = True

    def to_dict(self):
        return vars(self)


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

    def to_dict(self):
        dict_obj = vars(self)
        dict_obj["races"] = [race.to_dict() if race is not None else None for race in self.races]
        return dict_obj


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


class DBHandler:
    def __init__(self):
        with open("db_pass") as file:
            password = file.read()

        uri = f"mongodb+srv://admin:{password}@cluster0.qwkdptn.mongodb.net/?retryWrites=true&w=majority"

        self.db = MongoClient(uri).get_database("Wikipedia")

    def reset(self, col_name):
        self.db.drop_collection(col_name)
        self.db.create_collection(col_name)

    def add_races(self, races: List[DBRace]):
        col = self.db.get_collection("Races")
        col.insert_many([race.to_dict() for race in races])

    def add_drivers(self, drivers: List[DBDriver]):
        col = self.db.get_collection("Drivers")
        col.insert_many([driver.to_dict() for driver in drivers])
