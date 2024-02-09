from typing import List
from urllib.request import urlopen
from bs4 import BeautifulSoup

from db import DBPointsPeriod, DBDriver, DBRace


def parse_period_table(header_id: str, width: int):
    # get wiki page and parse
    html = (urlopen("https://en.wikipedia.org/wiki/List_of_Formula_One_World_Championship_points_scoring_systems")
            .read().decode("utf-8"))
    soup = BeautifulSoup(html, "html.parser")

    # find starting point with id
    starting_point = soup.find(id=header_id)
    assert starting_point is not None

    # navigate to wanted table
    table = starting_point.parent.find_next_sibling("table").find("tbody")

    # iterate over points periods
    db_points_periods = []
    points_period = table.find("tr").find_next_sibling("tr")
    while points_period is not None:
        cell_pointer = points_period.find("th")

        # handle rows with no year
        if cell_pointer is not None:
            start_year = int(list(cell_pointer.stripped_strings)[0])

            # expect 'width' cells
            full_row = True
            points = {}
            for i in range(1, width + 1):
                cell_pointer = cell_pointer.find_next_sibling("td")
                if cell_pointer is None:
                    full_row = False
                    break

                # parse cell contents
                points_for_pos = list(cell_pointer.stripped_strings)[0]
                if points_for_pos.isnumeric():
                    points[i] = int(points_for_pos)

                # special 1961 case
                elif len(list(cell_pointer.stripped_strings)) > 1:
                    num = points_for_pos[:1]
                    if num.isnumeric():
                        points[i] = int(num)

            if full_row:
                # end previous period
                if len(db_points_periods) > 0:
                    db_points_periods[-1].end = start_year - 1

                db_points_period = DBPointsPeriod()
                db_points_periods.append(db_points_period)
                db_points_period.start = start_year
                db_points_period.points_distribution = points
                if start_year == 1950:
                    db_points_period.fastest_lap_always = True

        # set next points period
        points_period = points_period.find_next_sibling("tr")

    return db_points_periods


def get_corresponding_system(driver: DBDriver, points_periods: List[DBPointsPeriod]):
    for points_period in points_periods:
        if (points_period.start <= driver.year
                and (points_period.end is None or driver.year <= points_period.end)):
            return points_period


class PointsHandler:

    def __init__(self):
        self.points_periods = parse_period_table("Points_scoring_systems", 11)
        self.sprint_periods = parse_period_table("Special_cases", 8)

    def get_points_period(self, driver: DBDriver):
        points_period = get_corresponding_system(driver, self.points_periods)
        assert points_period is not None
        return points_period

    def get_sprint_period(self, driver: DBDriver):
        return get_corresponding_system(driver, self.sprint_periods)

    def calculate_points(self, driver: DBDriver, races: List[DBRace]):
        total_points = [0]
        points_per_race = []

        points_system = self.get_points_period(driver)
        points_table = points_system.points_distribution

        sprint_system = self.get_sprint_period(driver)

        for i, race_result in enumerate(driver.races):
            if race_result is None:
                total_points.append(total_points[-1])
                points_per_race.append(0)
                continue

            # 11 is fastest lap index
            got_fastest = 11 in points_table and race_result.fastest_lap

            if isinstance(race_result.position, int) and race_result.position in points_table:
                race_result.points += points_table[race_result.position] * races[i].scoring_modifier

                if got_fastest and not points_system.fastest_lap_always:
                    race_result.points += points_table[11]

            if got_fastest and points_system.fastest_lap_always:
                race_result.points += points_table[11]

            if race_result.sprint_result is not None:
                race_result.points += sprint_system.points_distribution[race_result.sprint_result]

            driver.total_points += race_result.points
