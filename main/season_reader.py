from urllib.request import urlopen

from bs4 import BeautifulSoup

from main.db import DBRace, DBDriver, DBRaceResult
from main.points import PointsHandler


class SeasonReader:
    def __init__(self):
        self.points_handler = PointsHandler()

    def get_races_and_drivers(self, year: int):
        # get wiki page and parse
        page = f"https://en.wikipedia.org/wiki/{year}_Formula_One_{"World_Championship" if year > 1980 else "season"}"
        html = (urlopen(page).read().decode("utf-8"))
        soup = BeautifulSoup(html, "html.parser")

        # find starting point with id
        starting_point = soup.find(id="World_Drivers'_Championship_standings")
        assert starting_point is not None

        # navigate to wanted table
        cur_element = starting_point.parent.find_next_sibling()
        if cur_element.name == "div":
            cur_element = cur_element.find("table")
        elif cur_element.name != "table":
            cur_element = cur_element.find_next_sibling("table")
        table = cur_element.find("tbody").find("tr").find("td").find("table").find("tbody")

        # iterate over races in first row
        db_races = []
        races = table.find("tr")
        cur_race = races.find("th").find_next_sibling().find_next_sibling()
        cur_index = 1
        while cur_race is not None:
            if cur_race.find("span") is None:
                break

            race_info = list(cur_race.stripped_strings)

            db_race = DBRace()
            db_races.append(db_race)

            db_race.name = race_info[0]
            db_race.year = year
            if len(race_info) > 1:
                db_race.scoring_modifier = 0.5
            db_race.flag_link = cur_race.find("span", class_="flagicon").find("span").find("a").find("img").attrs["src"]
            db_race.index = cur_index

            # set next race
            cur_race = cur_race.find_next_sibling()
            cur_index += 1

        # iterate over driver rows
        db_drivers = []
        cur_driver = races.find_next_sibling("tr")
        while cur_driver is not None:
            if cur_driver.find("th") is None or cur_driver.find("td") is None:
                break

            db_driver = DBDriver()
            db_driver.year = year
            db_drivers.append(db_driver)

            # get info from driver row
            champ_pos = list(cur_driver.find("th").stripped_strings)[0]
            # take previous position for ties
            db_driver.championship_position = db_drivers[-2].championship_position \
                if champ_pos == "=" \
                else int(champ_pos) if champ_pos.isnumeric() else None

            name_cell = cur_driver.find("td")
            db_driver.name = list(name_cell.stripped_strings)[0]

            # iterate over races
            cur_race = name_cell.find_next_sibling("td")
            for _ in range(len(db_races)):
                cur_race_info = list(cur_race.stripped_strings)

                if len(cur_race_info) == 0:
                    db_driver.races.append(None)
                else:
                    db_race_result = DBRaceResult()
                    db_driver.races.append(db_race_result)

                    main_info = cur_race_info.pop(0)
                    if "\u2020" in main_info:  # dagger cross for race not finished but classified
                        main_info = main_info.replace("\u2020", "")
                    if "\u2021" in main_info:  # another irrelevant character
                        main_info = main_info.replace("\u2021", "")
                    if "(" in main_info and ")" in main_info:
                        db_race_result.counts_for_total = False
                        main_info = main_info.replace("(", "").replace(")", "")
                    if "*" in main_info:
                        main_info = "NEP"  # not eligible for points

                    if main_info.isnumeric():
                        db_race_result.position = int(main_info)
                    elif main_info.isalpha():
                        db_race_result.position = main_info
                    else:
                        raise RuntimeError(f"weird main info: {main_info}")

                    # handle main info extras
                    if cur_race.find("i") is not None:
                        db_race_result.fastest_lap = True
                        if cur_race.find("i").find("b") is not None:
                            db_race_result.pole = True

                    # handle annotations
                    if len(cur_race_info) > 0:
                        # handle case when all annotations in one block
                        if " " in cur_race_info[0]:
                            if len(cur_race_info) > 1:
                                print(f"weird annotation: {cur_race_info}")
                            else:
                                cur_race_info = cur_race_info[0].split(" ")

                        if "P" in cur_race_info:
                            db_race_result.pole = True
                            cur_race_info.remove("P")
                        if "F" in cur_race_info:
                            db_race_result.fastest_lap = True
                            cur_race_info.remove("F")
                        if "PF" in cur_race_info:
                            db_race_result.pole = True
                            db_race_result.fastest_lap = True
                            cur_race_info.remove("PF")
                        if "\u2020" in cur_race_info:  # dagger cross for race not finished but classified
                            cur_race_info.remove("\u2020")
                        if "1" in cur_race_info and self.points_handler.get_sprint_period(db_driver) is None:
                            cur_race_info.remove("1")
                        if len(cur_race_info) > 0 and cur_race_info[0].isnumeric():
                            db_race_result.sprint_result = int(cur_race_info.pop(0))
                        # if len(cur_race_info) > 0:
                        #     print(f"unexpected annotations: {cur_race_info}")

                # set next race
                cur_race = cur_race.find_next_sibling("td")

            # set next driver
            cur_driver = cur_driver.find_next_sibling("tr")

        for driver in db_drivers:
            self.points_handler.calculate_points(driver, db_races)

        return db_races, db_drivers
