import os, re, sys
import datetime
from pyquery import PyQuery as pq
from collections import defaultdict
from src.season import Season
from src.models import DATABASE, reset_database, Team, Game, Actor, Participant


def fill_dict(array):
    to_return = dict()
    none_list = ['actor', 'number']
    for i in array:
        to_return[i] = None if i in none_list else 0
    return to_return


def replace_nth_ocurrence(source, n, letter, new_value):
    ind = source.index(letter, n)
    source[ind] = new_value
    return source


def get_game_and_teams(raw_game, id_game_number, season, competition_phase='regular', round_phase=None):
    """
    We extract all the information regarding the game such as the date, attendance, venue, score per quarter or teams.
    Therefore, we need first to extract and insert the teams in the database in order to get the references to the db.

    :param raw_game: String
    :param id_game_number: int
    :param season: Season
    :param competition_phase: String
    :param round_phase: String
    :return: Game object
    """

    """
    There are two different statistics table in acb.com. I assume they created the new one to introduce the +/- stat.
    """
    estadisticas_tag = '.estadisticasnew' if re.search(r'<table class="estadisticasnew"', raw_game) else '.estadisticas'

    doc = pq(raw_game)
    game_dict = dict()

    """
    Each game has an unique id in acb.com. The id has 5 digits, where the first two digits are the season code (the
    oldest season in 1956 has code 1) and the three last are the number of the game (a simple counter since the beginning
    of the season).

    Usually you can use this id to access the concrete game within the link 'http://www.acb.com/fichas/LACBXXYYY.php'
    However, for older seasons, this link might be not available. TODO: find out exactly in which season.
    """
    game_dict['acbid'] = str(season.season_id).zfill(2,) + str(id_game_number).zfill(3)
    game_dict['competition_phase'] = competition_phase
    game_dict['round'] = round_phase
    
    # Information about the teams.
    info_teams_data = doc(estadisticas_tag).eq(1)

    """
    We only have the names of the teams (text) within the doc. Hence, we need to get the teams' ids from other source
    in order to introduce such information in the database.

    Full disclosure: we get these ids from the standing page.
    """
    teams_ids = season.get_teams_ids()

    for i in [0, 2]:
        team_data = info_teams_data('.estverde').eq(i)('td').eq(0).text()
        team_name, score = re.search("(.*) ([1]?[0-9][0-9])", team_data).groups()

        """
        We create a team per season since a team can have different names along its history. Anyway, same teams
        will have same acbid.
        """
        team = Team.get_or_create(**{'acbid': teams_ids[team_name], 'name': team_name, 'season': season.season})[0]
        game_dict['team_home_id' if i == 0 else 'team_away_id'] = team
        game_dict['score_home' if i == 0 else 'score_away'] = int(score)

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
        game_dict['attendance'] = int(attendance.split(":")[1])

    if venue:
        game_dict['venue'] = venue

    if journey:
        game_dict['journey'] = journey.split(" ")[1]

    for i in range(2,7):
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
            game_dict[score_home_attribute], game_dict[score_away_attribute] = list(map(int, quarter_data.split("|")))

    game = Game.get_or_create(**game_dict)[0]
    return game


def get_referees(raw_game, game):
    """
    Extract and introduce in the database the referees of the game.

    :param raw_game: String
    :return: List of Referee objects
    """

    estadisticas_tag = '.estadisticasnew' if re.search(r'<table class="estadisticasnew"', raw_game) else '.estadisticas'
    doc = pq(raw_game)
    info_game_data = doc(estadisticas_tag).eq(0)
    referees_data = info_game_data('.estnaranja')('td').eq(0).text()
    referees = None
    if referees_data:
        referees = referees_data.split(":")[1].strip().split(",")
        referees = list(filter(None, referees))
        referees = list(map(lambda x: x.strip(), referees))

    """
    We only have information about the name of a referee.
    """
    for referee in referees:
        Participant.create(**{'display_name': referee, 'game': game, 'is_referee': 1})

    return referees


def get_participants_and_actors(raw_game, game):
    """

    :param raw_game: String
    :param game: Game object
    :return: List of Participant objects and list of Actor objects.
    """
    estadisticas_tag = '.estadisticasnew' if re.search(r'<table class="estadisticasnew"', raw_game) else '.estadisticas'
    doc = pq(raw_game)
    info_players_data = doc(estadisticas_tag).eq(1)

    """
    We make sure we only retrieve stats that are in the header. One clear example can be found when the estadisticas_tag
    is 'estadisticas' since it hasn't got the +/- stat.
    """
    header_text = info_players_data('tr').eq(1)
    header = []
    for index in header_text('td').items():
        header.append(index.text())


    """
    However, the acb ids of the stats are not unique and some of then are repeteated.
    We have three times a 'C' and two times a 'F'. We manually modify these ids.
    """
    # The first C is counterattack, the second C is received_block and the third received_fault.
    header = replace_nth_ocurrence(header, 2, "C", "TAPC")
    header = replace_nth_ocurrence(header, 2, "C", "FPC")
    # The first F is block and the second F is  fault.
    header = replace_nth_ocurrence(header, 1, "F", "TAPF")
    header = replace_nth_ocurrence(header, 1, "F", "FPF")

    """
    We create the correspondance between the acb ids and the attributes in our database
    """
    header_to_db = {'D': 'number', 'Nombre': "display_name", 'Min': 'minutes', 'P': 'point', 'T2': 't2',
                    'T3': 't3', 'T1': 't1', 'REBD': 'defensive_reb', 'REBO': 'offensive_reb', 'A': 'assist',
                    'BR': 'steal', 'BP': 'turnover', 'C': 'counterattack', 'TAPF': 'block',
                    'TAPC': 'received_block', 'M': 'dunk', 'FPF': 'fault', 'FPC': 'received_fault',
                    '+/-': 'plus_minus', 'V': 'efficiency'}

    """
    Let us remove the database attributes that are not included in the header.
    """
    # Preventing from missing stats
    for key, match in list(header_to_db.items()):
        if key not in header:
            header_to_db.pop(key)

    """
    We add extra attributes that are not inferred directly from the stats, but from the context.
    """
    header_to_db.update({"is_coach": "is_coach",
                         "is_referee": "is_referee",
                         "is_starter": "is_starter",
                         "game": "game",
                         "team": "team",
                         "actor": "actor",
                         "t1_attempt": "t1_attempt",
                         "t2_attempt": "t2_attempt",
                         "t3_attempt": "t3_attempt",
                         "defensive_reb": "defensive_reb",
                         "offensive_reb": "offensive_reb"})

    """
    We create a dictionary that contains, for each of the teams, and for each of the player, and for each of the stats
    the value of such stat for such player of such team.

    > stats[team][player][stat]

    where 'team' is the name of the team, 'player' is the number of the player and 'stat' is the acb stat id.
    """
    stats = defaultdict(dict)
    current_team = None
    for tr in info_players_data('tr').items():  # iterate over each row
        if tr('.estverde'): # header
            if tr.eq(0)('.estverdel'): # team information
                current_team = game.team_away.name if current_team else game.team_home.name  # first team home team
                stats[current_team] = defaultdict(dict)
            else:  # omit indexes
                pass
        else:  # players, equipo, and coach.
            number = None
            for cont, td in enumerate(tr('td').items()):  # iterate over each cell (stat)
                if td.text() == "5f" or td.text() == 'Total':  # 5f nor Total are not players.
                    break

                elif cont == 0:  # first cell number of the player
                    number = td.text() if td.text() else 'Equipo'
                    if number in stats[current_team]:  # preventing from errors with the number.
                        raise ValueError('Number {} does already exist!'.format(number))
                    else:
                        # Create the dict with default attributes.
                        stats[current_team][number] = fill_dict(header_to_db.values())
                        stats[current_team][number]['is_starter'] = 1 if td('.gristit') else 0
                        stats[current_team][number]['game'] = game
                        stats[current_team][number]['team'] = game.team_home if current_team == game.team_home.name else game.team_away

                elif cont == 1 and td('a'): # second cell player id
                    href_attribute = td('a').attr('href').split("=")  # the acb id is in the href attribute.
                    stats[current_team][number]['id'] = href_attribute[-1]

                    is_coach = re.search(r'entrenador', href_attribute[0])
                    stats[current_team][number]['is_coach'] = 1 if is_coach else 0
                    stats[current_team][number]['is_referee'] = 0
                    stats[current_team][number]['number'] = None if is_coach else int(number)
                    stats[current_team][number]['display_name'] = td.text()

                elif '%' in header[cont]:  # discard percentages.
                    continue

                elif '/' in td.text():  # T1, T2 or T3 in format success/attempts.
                    success, attempts = td.text().split("/")
                    stats[current_team][number][header_to_db[header[cont]]] = int(success)
                    stats[current_team][number][header_to_db[header[cont]]+"_attempt"] = int(attempts)

                elif '+' in td.text():  # defensive and offensive rebounds in format D+O
                    defensive, offensive = td.text().split("+")
                    stats[current_team][number]["defensive_reb"] = int(defensive)
                    stats[current_team][number]["offensive_reb"] = int(offensive)

                elif ':' in td.text():  # minutes in format minutes:seconds
                    minutes, seconds = td.text().split(":")
                    stats[current_team][number]["minutes"] = int(minutes)*60+int(seconds)

                else:
                    if header[cont] in header_to_db:  # only add useful stats.
                        try:
                            stats[current_team][number][header_to_db[header[cont]]] = int(td.text()) if td.text() else 0
                        except:
                            stats[current_team][number][header_to_db[header[cont]]] = td.text()

    """
    We now insert the participants of the game in the database.
    Therefore, we need first to get or create the actors in the database.

    We consider an actor as a player or a coach. We don't have informationa about referees so we don't include
    them here.
    """
    to_insert_many_participants = []
    actors = []
    for team, team_dict in stats.items():
        for player, player_stats in team_dict.items():
            try:
                actor = Actor.get_or_create(acbid=stats[team][player]['id'])
                if actor[1]:
                    actor[0].display_name = stats[team][player]['display_name']
                    actor[0].save()
                    actors.append(actor)
                stats[team][player]['actor'] = actor[0]
                stats[team][player].pop('id')
            except:
                pass
            to_insert_many_participants.append(stats[team][player])
    participants = Participant.insert_many(to_insert_many_participants).execute()
    return participants, actors


def main():
    reset_database()
    year = 2015
    season = Season(year)
    id_game_number = 1
    competition_phase = 'regular'
    round_phase = None

    with open(os.path.join('..', 'data', str(year), str(id_game_number)+'.html')) as f:
        raw_game = f.read()

    with DATABASE.atomic():
        game = get_game_and_teams(raw_game=raw_game, id_game_number=id_game_number,
                                                                     season=season,
                                               competition_phase=competition_phase,
                                                           round_phase=round_phase)

        referees = get_referees(raw_game=raw_game, game=game)
        participants, actors = get_participants_and_actors(raw_game=raw_game, game=game)

if __name__ == "__main__":
    main()

