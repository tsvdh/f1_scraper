from tqdm import tqdm

from main.db import DBHandler
from main.season_reader import SeasonReader

if __name__ == "__main__":
    db = DBHandler()
    db.reset("Races")
    db.reset("Drivers")

    season_reader = SeasonReader()

    years = range(1964, 2024)

    # supports until 1964
    for year in tqdm(years):
        races, drivers = season_reader.get_races_and_drivers(year)

        db.add_races(races)
        db.add_drivers(drivers)
