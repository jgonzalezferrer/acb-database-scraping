import os.path, re, datetime, difflib, logging
from pyquery import PyQuery as pq
from src.download import open_or_download, sanity_check
from src.season import BASE_URL
from models.basemodel import BaseModel
from models.team import Team, TeamName
from peewee import (PrimaryKeyField, TextField, IntegerField,
                    DateTimeField, ForeignKeyField, BooleanField)


class Game(BaseModel):
    """
    Class representing a Game.

    A game only contains basic information about the game and the scores.
    """
    id = PrimaryKeyField()
    acbid = TextField(unique=True, index=True)
    team_home = ForeignKeyField(Team, related_name='games_home', index=True, null=True)
    team_away = ForeignKeyField(Team, related_name='games_away', index=True, null=True)
    competition_phase = TextField(null=True)
    round_phase = TextField(null=True)
    journey = IntegerField(null=True)
    venue = TextField(null=True)
    attendance = IntegerField(null=True)
    kickoff_time = DateTimeField(index=True)
    score_home = IntegerField(null=True)
    score_away = IntegerField(null=True)
    score_home_first = IntegerField(null=True)
    score_away_first = IntegerField(null=True)
    score_home_second = IntegerField(null=True)
    score_away_second = IntegerField(null=True)
    score_home_third = IntegerField(null=True)
    score_away_third = IntegerField(null=True)
    score_home_fourth = IntegerField(null=True)
    score_away_fourth = IntegerField(null=True)
    score_home_extra = IntegerField(null=True)
    score_away_extra = IntegerField(null=True)
    db_flag = BooleanField(null=True)

    @staticmethod
    def save_games(season, logging_level=logging.INFO):
        """
        Method for saving locally the games of a season.

        :param season: int
        :param logging_level: logging object
        :return:
        """
        logging.basicConfig(level=logging_level)
        logger = logging.getLogger(__name__)

        logger.info('Starting downloading...')
        n_games = season.get_number_games()
        for game_id in range(1, n_games + 1):
            filename = os.path.join(season.GAMES_PATH, str(game_id) + '.html')
            url = BASE_URL + "stspartido.php?cod_competicion=LACB&cod_edicion={}&partido={}".format(season.season_id,
                                                                                                    game_id)
            open_or_download(file_path=filename, url=url)
            if game_id % (round(n_games / 3)) == 0:
                logger.info('{}% already downloaded'.format(round(float(game_id) / n_games * 100)))

        logger.info('Downloading finished! (new {} games in {})'.format(n_games, season.GAMES_PATH))

    @staticmethod
    def sanity_check(season, logging_level=logging.INFO):
        sanity_check(season.GAMES_PATH, logging_level)

    @staticmethod
    def create_instance(raw_game, id_game_number, season, competition_phase='regular', round_phase=None):
        """
        Extract all the information regarding the game such as the date, attendance, venue, score per quarter or teams.
        Therefore, we need first to extract and insert the teams in the database in order to get the references to the db.

        :param raw_game: String
        :param id_game_number: int
        :param season: Season
        :param competition_phase: String
        :param round_phase: String
        :return: Game object
        """

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        """
        There are two different statistics table in acb.com.
        I assume they created the new one to introduce the +/- stat.
        """
        estadisticas_tag = '.estadisticasnew' if re.search(r'<table class="estadisticasnew"',
                                                           raw_game) else '.estadisticas'

        doc = pq(raw_game)
        game_dict = dict()

        """
        Each game has an unique id in acb.com. The id has 5 digits, where the first two digits are the season code (the
        oldest season in 1956 has code 1) and the three last are the number of the game (a simple counter since the beginning
        of the season).

        This id can be used to access the concrete game within the link 'http://www.acb.com/fichas/LACBXXYYY.php'
        """
        game_dict['acbid'] = str(season.season_id).zfill(2) + str(id_game_number).zfill(3)
        game_dict['competition_phase'] = competition_phase
        game_dict['round_phase'] = round_phase

        # Information about the teams.
        info_teams_data = doc(estadisticas_tag).eq(1)
        home_team_name = None
        away_team_name = None

        """
        We only have the names of the teams (text) within the doc. Hence, we need to get the teams' ids from other
        source in order to introduce such information in the database.

        Full disclosure: we get these ids from the standing page. If we the standing page is not available (it might
        happensin old seasons), we try to make a match with existing teams. If this match doesn't exist, we need to
        harcode the team and its id correspondance.
        """
        teams_ids = season.get_teams_ids()
        for i in [0, 2]:
            team_data = info_teams_data('.estverde').eq(i)('td').eq(0).text()
            team_name = re.search("(.*) [0-9]", team_data).groups()[0]
            """
            We create a team per season since a team can have different names along its history. Anyway, same teams
            will have same acbid.

            Note: ACB doesn't agree in teams names and sometimes write the same name in different ways.
            E.g.:

             - VALENCIA BASKET instead of VALENCIA BASKET CLUB
             - C.B. OURENSE instead of CB OURENSE
            """
            try:
                if len(teams_ids):  # if the standing page exists.
                    team_acbid = teams_ids[team_name]
                else:
                    team_acbid = TeamName.get(TeamName.name == team_name).team.acbid
                team = Team.get(Team.acbid == team_acbid)

            except KeyError:  # we don't find an exact correspondance, let's find the closest match.
                if season.season in list(Team.get_harcoded_teams().keys()) \
                        and team_name in list(Team.get_harcoded_teams()[season.season].keys()):  # harcoded team?
                    team = Team.get(Team.acbid == Team.get_harcoded_teams()[season.season][team_name])
                else:
                    most_likely_team = difflib.get_close_matches(team_name, teams_ids.keys(), 1, 0.4)[0]
                    team = Team.get(Team.acbid == teams_ids[most_likely_team])

                    if most_likely_team not in season.mismatched_teams:  # debug info to check the correctness.
                        season.mismatched_teams.append(most_likely_team)
                        logger.info('Season {} -> {} has been matched to: {}'.format(season.season,
                                                                                     team_name,
                                                                                     most_likely_team))

            TeamName.get_or_create(**{'team': team, 'name': team_name, 'season': season.season})
            game_dict['team_home_id' if i == 0 else 'team_away_id'] = team
            home_team_name = team_name if i == 0 else home_team_name
            away_team_name = team_name if i != 0 else away_team_name

        # Information about the game.
        info_game_data = doc(estadisticas_tag).eq(0)

        scheduling_data = info_game_data('.estnegro')('td').eq(0).text()
        scheduling_data = scheduling_data.split("|")
        journey, date, time, venue, attendance = list(map(lambda x: x.strip(), scheduling_data))  # Remove extra spaces.

        if date and time:
            day, month, year = list(map(int, date.split("/")))
            hour, minute = list(map(int, time.split(":")))
            game_dict['kickoff_time'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

        if attendance:
            try:
                game_dict['attendance'] = int(attendance.split(":")[1])
            except ValueError:
                pass

        if venue:
            game_dict['venue'] = venue

        if journey:
            game_dict['journey'] = journey.split(" ")[1]

        for i in range(2, 7):
            score_home_attribute = ''
            score_away_attribute = ''
            if i == 2:
                score_home_attribute = 'score_home_first'
                score_away_attribute = 'score_away_first'
            elif i == 3:
                score_home_attribute = 'score_home_second'
                score_away_attribute = 'score_away_second'
            elif i == 4:
                score_home_attribute = 'score_home_third'
                score_away_attribute = 'score_away_third'
            elif i == 5:
                score_home_attribute = 'score_home_fourth'
                score_away_attribute = 'score_away_fourth'
            elif i == 6:
                score_home_attribute = 'score_home_extra'
                score_away_attribute = 'score_away_extra'

            quarter_data = info_game_data('.estnaranja')('td').eq(i).text()
            if quarter_data:
                try:
                    game_dict[score_home_attribute], game_dict[score_away_attribute] = list(
                        map(int, quarter_data.split("|")))
                except ValueError:
                    pass

        try:
            game = Game.get(Game.acbid == game_dict['acbid'])
        except:
            game = Game.create(**game_dict)
        return game