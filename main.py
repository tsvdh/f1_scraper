from main.season_reader import SeasonReader

if __name__ == "__main__":
    season_reader = SeasonReader()
    year = 2023

    # supports until 1964
    while year >= 1964:
        print(year)
        season_reader.get_races_and_drivers(year)
        year -= 1
