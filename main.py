from urllib.request import urlopen
from bs4 import BeautifulSoup
from db import DBRace, DBDriver, DBRaceResult
from points import PointsHandler


def get_races_and_drivers(year: int):
    # get wiki page and parse
    html = (urlopen(f"https://en.wikipedia.org/wiki/{year}_Formula_One_World_Championship")
            .read().decode("utf-8"))
    soup = BeautifulSoup(html, "html.parser")

    # find starting point with id
    starting_point = soup.find(id="World_Drivers'_Championship_standings")
    assert starting_point is not None

    # navigate to wanted table
    cur_element = starting_point.parent.find_next_sibling()
    if cur_element.name == "div":
        cur_element = cur_element.find("table")
    table = cur_element.find("tbody").find("tr").find("td").find("table").find("tbody")

    # get info from races row
    db_races = []
    races = table.find("tr")
    for race in races.find_all("th")[2:-1]:
        race_info = list(race.stripped_strings)

        db_race = DBRace()
        db_races.append(db_race)

        db_race.name = race_info[0]
        db_race.year = year
        if len(race_info) > 1:
            db_race.scoring_modifier = 0.5

    # iterate over driver rows
    db_drivers = []
    cur_driver = races.find_next_sibling("tr")
    while cur_driver is not None:
        if cur_driver.find("td") is None:
            break

        db_driver = DBDriver()
        db_driver.year = year
        db_drivers.append(db_driver)

        # get info from driver row
        db_driver.championship_position = cur_driver.find("th").string.strip()
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

                # three race classification options
                main_info = cur_race_info.pop(0)
                if main_info.isnumeric():
                    db_race_result.position = int(main_info)
                elif main_info.isalpha():
                    db_race_result.position = main_info
                elif "\u2020" in main_info:  # dagger cross for race not finished but classified
                    db_race_result.position = int(main_info.replace("\u2020", ""))
                else:
                    print(f"weird main info: {main_info}")

                # db_race_result.points +=

                if len(cur_race_info) > 0:
                    # handle case when all annotations in one block
                    if " " in cur_race_info[0]:
                        # print(f"weird annotation: {cur_race_info}")
                        cur_race_info = cur_race_info[0].split(" ")

                    if "P" in cur_race_info:
                        db_race_result.pole = True
                        cur_race_info.remove("P")
                    if "F" in cur_race_info:
                        db_race_result.fastest_lap = True
                        cur_race_info.remove("F")
                    if "\u2020" in cur_race_info:  # dagger cross for race not finished but classified
                        cur_race_info.remove("\u2020")
                    if len(cur_race_info) > 0:
                        db_race_result.sprint_result = int(cur_race_info.pop(0))
                    if len(cur_race_info) > 0:
                        print(f"unexpected annotations: {cur_race_info}")

            # set next race
            cur_race = cur_race.find_next_sibling("td")

        # set next driver
        cur_driver = cur_driver.find_next_sibling("tr")

    points_handler = PointsHandler()

    for driver in db_drivers:
        points_handler.calculate_points(driver, db_races)

    return db_races, db_drivers


if __name__ == "__main__":
    season_races, season_drivers = get_races_and_drivers(2023)
    print(season_drivers[:2])
