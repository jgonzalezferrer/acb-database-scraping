import os, re
import numpy as np
from pyquery import PyQuery as pq
from src.download import validate_dir, open_or_download


FIRST_SEASON = 1956
BASE_URL = 'http://www.acb.com/'
DATA_PATH = '../data'
TEAMS_PATH = os.path.join(DATA_PATH, 'teams')
ACTORS_PATH = os.path.join(DATA_PATH, 'actors')
PLAYERS_PATH = os.path.join(ACTORS_PATH, 'players')
COACHES_PATH = os.path.join(ACTORS_PATH, 'coaches')

validate_dir(TEAMS_PATH)
validate_dir(ACTORS_PATH)
validate_dir(PLAYERS_PATH)
validate_dir(COACHES_PATH)


class Season:
    def __init__(self, season):
        self.season = season
        self.season_id = season - FIRST_SEASON + 1  # First season in 1956 noted as 1.
        self.SEASON_PATH = os.path.join(DATA_PATH, str(self.season))
        self.GAMES_PATH = os.path.join(self.SEASON_PATH, 'games')
        validate_dir(self.SEASON_PATH)
        validate_dir(self.GAMES_PATH)

        self.relegation_playoff_seasons = [1994, 1995, 1996, 1997]
        self.missing_playoff_format = [1994, 1995]
        self.num_teams = self.get_number_teams()
        self.playoff_format = self.get_playoff_format()
        self.mismatched_teams = []

    def save_teams(self):
        filename = os.path.join(self.SEASON_PATH, 'teams' + '.html')
        # There is a bug in 2007 that the first journey has duplicated teams.
        url = BASE_URL + "resulcla.php?codigo=LACB-{}&jornada=2".format(self.season_id)
        return open_or_download(file_path=filename, url=url)

    def get_number_teams(self):
        content = self.save_teams()
        teams_match = re.findall(r'<td class="rojo" align="right"><b>([0-9]+)</b>', content, re.DOTALL)
        if len(teams_match) == 0:  # from 1994 and backward there isn't standings, we just count the games
            return len(re.findall(r'http://www.acb.com/imgs//flechitaroja.gif', content, re.DOTALL))*2
        else:
            return len(teams_match)

    def get_teams_ids(self):
        content = self.save_teams()
        teams_doc = pq(content)
        teams_tag = '.resultados2'
        teams_info = teams_doc(teams_tag)('tr')('a')

        teams_ids = dict()
        for team in teams_info.items():
            id = re.search(r'id=(.*)', team.attr('href')).group(1)
            teams_ids[team.text().upper()] = id

        return teams_ids

    def get_playoff_round_format(self, page, round_tag):
        doc = pq(page)
        round_format = doc(round_tag)
        round_format = round_format(".resultado-equipo").text().split(" ")
        round_format = list(map(int, round_format))
        round_format = 2 * round_format[0] - 1 if round_format[0] > round_format[1] else 2 * round_format[1] - 1
        return round_format

    def get_playoff_format(self):
        if self.season in self.missing_playoff_format:
            return [3, 5, 5]  # page 32 in http://www.acb.com/publicaciones/guia1995
        else:
            filename = os.path.join(self.SEASON_PATH, 'playoff.html')
            url = BASE_URL + "playoff.php?cod_competicion=LACB&cod_edicion={}".format(self.season_id)
            content = open_or_download(file_path=filename, url=url)

            playoff_format = list()
            playoff_format.append(self.get_playoff_round_format(content, "#columnacuartos"))
            playoff_format.append(self.get_playoff_round_format(content, "#columnasemi"))
            playoff_format.append(self.get_playoff_round_format(content, "#columnafinal"))
            return playoff_format

    def get_number_games_regular_season(self):
        return (self.num_teams - 1) * self.num_teams

    def get_number_games_playoff(self):
        games_per_round = [4, 2, 1]  # Quarter-finals, semifinals, final.
        return sum(np.array(self.playoff_format) * np.array(games_per_round))  # Element-wise multiplication.

    def get_number_games(self):
        return self.get_number_games_regular_season() + self.get_number_games_playoff() + self.get_number_games_relegation_playoff()

    def get_number_games_relegation_playoff(self):
        return 5*2 if self.season in self.relegation_playoff_seasons else 0

    def get_relegation_teams(self):
        if self.season <= 1994:
            return {1994: ['VALVI GIRONA', 'BREOGÁN LUGO', 'PAMESA VALENCIA', 'SOMONTANO HUESCA']}[self.season]
        else:
            filename = os.path.join(self.SEASON_PATH, 'relegation_playoff.html')
            url = BASE_URL + "resulcla.php?codigo=LACB-{}&jornada={}".format(self.season_id, (self.get_number_teams()-1)*2)
            content = open_or_download(file_path=filename, url=url)
            doc = pq(content)
            relegation_teams = []
            for team_id in range(self.get_number_teams()-4, self.get_number_teams()):
                relegation_teams.append(doc('.negro').eq(team_id).text().upper())

            return relegation_teams