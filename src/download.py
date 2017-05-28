import urllib.request, os, re
import logging
import numpy as np
from pyquery import PyQuery as pq


BASE_URL = 'http://www.acb.com/'
DATA_PATH = '../data'


def get_page(url):
    """Get data from URL"""
    return urllib.request.urlopen(url).read()


def validate_dir(folder):
    """Creates a directory if it doesn't already exist."""
    if not os.path.exists(folder):
        os.mkdir(folder)


def save_file(file_path, content):
    """Saves the content to a file in the path provided"""
    file_obj = open(file_path, 'w')
    file_obj.write(content)
    file_obj.close


def save_game(season_id, game_id, output_path):
    filename = os.path.join(output_path, str(game_id) + '.html')

    if not os.path.isfile(filename):
        html_file = get_page(BASE_URL + "stspartido.php?cod_competicion=LACB&cod_edicion={}&partido={}"
                             .format(season_id, game_id))
        save_file(filename, html_file)


validate_dir(DATA_PATH)


class Season():
    global FIRST_SEASON
    FIRST_SEASON = 1956

    def __init__(self, season):
        self.season = season
        self.season_id = season - FIRST_SEASON + 1  # First season in 1956 noted as 1.
        self.SEASON_PATH = os.path.join(DATA_PATH, str(self.season))

        validate_dir(self.SEASON_PATH)
        self.num_teams = self.get_number_teams()
        self.playoff_format = self.get_playoff_format

    def get_number_teams(self):
        filename = os.path.join(self.SEASON_PATH, '0.html')
        if (not os.path.isfile(filename)):
            html_file = get_page(BASE_URL + "resulcla.php?codigo=LACB-{}".format(self.season_id))
            save_file(filename, html_file)

        with open(filename) as f:
            index_page = f.read()
            teams_match = re.findall('<td class="rojo" align="right"><b>([0-9]+)</b>', index_page, re.DOTALL)
            return len(teams_match)

    def get_round_format(self, page, round_tag):
        doc = pq(page)
        round_format = doc(round_tag)
        round_format = round_format(".resultado-equipo").text().split(" ")
        round_format = map(int, round_format)
        round_format = 2 * round_format[0] - 1 if round_format[0] > round_format[1] else 2 * round_format[1] - 1
        return round_format

    def get_playoff_format(self):
        filename = os.path.join(self.SEASON_PATH, 'playoff.html')
        if (not os.path.isfile(filename)):
            html_file = get_page(BASE_URL + "playoff.php?cod_competicion=LACB&cod_edicion={}".format(self.season_id))
            save_file(filename, html_file)

        playoff_format = []
        with open(filename) as f:
            index_page = f.read()
            playoff_format.append(self.get_round_format(index_page, "#columnacuartos"))
            playoff_format.append(self.get_round_format(index_page, "#columnasemi"))
            playoff_format.append(self.get_round_format(index_page, "#columnafinal"))
            return playoff_format

    def get_number_games_regular_season(self):
        return (self.num_teams - 1) * self.num_teams

    def get_number_games_playoff(self):
        games_per_round = [4, 2, 1]  # Quarter-finals, semifinals, final.
        return sum(np.array(self.playoff_format()) * np.array(games_per_round))  # Element-wise multiplication.

    def get_number_games(self):
        return self.get_number_games_regular_season() + self.get_number_games_playoff()

    def save_games(self, logging_level=logging.INFO):
        logging.basicConfig(level=logging_level)
        logger = logging.getLogger(__name__)

        logger.info('Starting downloading...')
        n_games = self.get_number_games()
        for game_id in range(1, n_games + 1):
            save_game(self.season_id, game_id, self.SEASON_PATH)
            if game_id % (n_games / 3) == 0: logger.info(
                '{}% already downloaded'.format(round(float(game_id) / n_games * 100)))

        logger.info('Downloading finished! (new {} games in {})'.format(n_games, self.SEASON_PATH))

    def sanity_check(self, logging_level=logging.INFO):
        logging.basicConfig(level=logging_level)
        logger = logging.getLogger(__name__)

        n_games = self.get_number_games()
        errors = []
        for game_id in range(1, n_games + 1):
            filename = os.path.join(self.SEASON_PATH, str(game_id) + '.html')
            with open(filename) as f:
                raw_html = f.read()
                doc = pq(raw_html)
                if doc("title").text() == '404 Not Found':
                    errors.append(game_id)

        if errors: raise Exception('There are {} errors in the downloads!'.format(len(errors)))
        logger.info('Sanity check finished!\n')
        return errors


#
# for season in range(2009, 2015):
#     obj = Season(season)
#     obj.save_games()
#     obj.sanity_check()

with open('/mnt/sda1/github-projects-outside-dropbox/scrapy/data/2015/1.html') as f:
    raw_html = f.read()

    doc = pq(raw_html)

    #  J 1 | 11/10/2015 | 19:00 | M.I. Govern Andorra | Público:3815
    info_game_data = doc('.estnegro')('td').eq(0).text()
    info_game_data = info_game_data.split("|")
    info_game_data = list(map(lambda x: x.strip(), info_game_data))  # Remove extra spaces.
    _, date, time, court, public = info_game_data

    day, month, year = date.split("/")
    public = public.split(":")[1]

    referees_data = doc('.estnaranja')('td').eq(0).text()
    referees = referees_data.split(":")[1].strip().split(",")
    referees = list(filter(None, referees))
    referees = list(map(lambda x: x.strip(), referees))

    first_quarter_data = doc('.estnaranja')('td').eq(2).text()
    first_quarter_home, first_quarter_away = first_quarter_data.split("|")

    second_quarter_data = doc('.estnaranja')('td').eq(3).text()
    second_quarter_home, second_quarter_away = second_quarter_data.split("|")

    third_quarter_data = doc('.estnaranja')('td').eq(4).text()
    third_quarter_home, third_quarter_away = third_quarter_data.split("|")

    fourth_quarter_data = doc('.estnaranja')('td').eq(5).text()
    fourth_quarter_home, fourth_quarter_away = fourth_quarter_data.split("|")

    extra_quarter_data = doc('.estnaranja')('td').eq(6).text()
    if extra_quarter_data:
        extra_quarter_home, extra_quarter_away = extra_quarter_data.split("|")

    home_team_data = doc('.estverde').eq(0)('td').eq(0).text()
    home_team, score_home = re.search("(.*) ([1]?[0-9][0-9])", home_team_data).groups()

    away_team_data = doc('.estverde').eq(2)('td').eq(0).text()
    away_team, score_away = re.search("(.*) ([1]?[0-9][0-9])", away_team_data).groups()

    
