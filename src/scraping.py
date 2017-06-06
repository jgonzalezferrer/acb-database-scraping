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


def get_game_and_teams(raw_game, game_number, season):
    estadisticas_tag = '.estadisticasnew' if re.search(r'<table class="estadisticasnew"', raw_game) else '.estadisticas'
    doc = pq(raw_game)
    info_game_data = doc(estadisticas_tag).eq(0)
    game_dict = dict()
    game_dict['acbid'] = int(str(season.season_id) + str(game_number).zfill(3))

    #  J 1 | 11/10/2015 | 19:00 | M.I. Govern Andorra | Público:3815
    scheduling_data = info_game_data('.estnegro')('td').eq(0).text()
    scheduling_data = scheduling_data.split("|")
    journey, date, time, venue, attendance = list(map(lambda x: x.strip(), scheduling_data))  # Remove extra spaces.

    day, month, year = list(map(int, date.split("/")))
    hour, minute = list(map(int, time.split(":")))
    game_dict['kickoff_time'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
    game_dict['attendance'] = int(attendance.split(":")[1])
    game_dict['venue'] = venue
    game_dict['journey'] = journey.split(" ")[1]

    first_quarter_data = info_game_data('.estnaranja')('td').eq(2).text()
    game_dict['score_home_first'], game_dict['score_away_first'] = list(map(int, first_quarter_data.split("|")))

    second_quarter_data = info_game_data('.estnaranja')('td').eq(3).text()
    game_dict['score_home_second'], game_dict['score_away_second'] = list(map(int, second_quarter_data.split("|")))

    third_quarter_data = info_game_data('.estnaranja')('td').eq(4).text()
    game_dict['score_home_third'], game_dict['score_away_third'] = list(map(int, third_quarter_data.split("|")))

    fourth_quarter_data = info_game_data('.estnaranja')('td').eq(5).text()
    game_dict['score_home_fourth'], game_dict['score_away_fourth'] = list(map(int, fourth_quarter_data.split("|")))

    extra_quarter_data = info_game_data('.estnaranja')('td').eq(6).text()
    if extra_quarter_data:
        game_dict['score_home_extra'], game_dict['score_away_extra'] = list(map(int, extra_quarter_data.split("|")))

    # Information about the players
    info_players_data = doc(estadisticas_tag).eq(1)
    teams_ids = season.get_teams_ids()

    home_team_data = info_players_data('.estverde').eq(0)('td').eq(0).text()
    home_team_name, score_home = re.search("(.*) ([1]?[0-9][0-9])", home_team_data).groups()
    home_team = Team.get_or_create(**{'acbid': teams_ids[home_team_name], 'name': home_team_name, 'season': season.season})[0]
    game_dict['team_home_id'] = home_team
    game_dict['score_home'] = int(score_home)

    away_team_data = info_players_data('.estverde').eq(2)('td').eq(0).text()
    away_team_name, score_away = re.search("(.*) ([1]?[0-9][0-9])", away_team_data).groups()
    away_team = Team.get_or_create(**{'acbid': teams_ids[away_team_name], 'name': away_team_name, 'season': season.season})[0]
    game_dict['team_away_id'] = away_team
    game_dict['score_away'] = int(score_away)

    game = Game.get_or_create(**game_dict)[0]

    return game, home_team, away_team


def get_referees(raw_game):
    estadisticas_tag = '.estadisticasnew' if re.search(r'<table class="estadisticasnew"', raw_game) else '.estadisticas'
    doc = pq(raw_game)
    info_game_data = doc(estadisticas_tag).eq(0)
    referees_data = info_game_data('.estnaranja')('td').eq(0).text()
    referees = referees_data.split(":")[1].strip().split(",")
    referees = list(filter(None, referees))
    referees = list(map(lambda x: x.strip(), referees))
    return referees


def get_participants_and_actors(raw_game, game, home_team, away_team):
    estadisticas_tag = '.estadisticasnew' if re.search(r'<table class="estadisticasnew"', raw_game) else '.estadisticas'
    doc = pq(raw_game)
    info_players_data = doc(estadisticas_tag).eq(1)
    header_text = info_players_data('tr').eq(1)
    header = []
    for index in header_text('td').items():
        header.append(index.text())

    # The ids of the stats are not unique.
    # The first C is counterattack, the second C is received_block and the third received_fault.
    header = replace_nth_ocurrence(header, 2, "C", "TAPC")
    header = replace_nth_ocurrence(header, 2, "C", "FPC")
    # The first F is block and the second F is  fault.
    header = replace_nth_ocurrence(header, 1, "F", "TAPF")
    header = replace_nth_ocurrence(header, 1, "F", "FPF")


    header_to_db = {'D': 'number', 'Nombre': "display_name", 'Min': 'minutes', 'P': 'point', 'T2': 't2',
                    'T3': 't3', 'T1': 't1', 'REBD': 'defensive_reb', 'REBO': 'offensive_reb', 'A': 'assist',
                    'BR': 'steal', 'BP': 'turnover', 'C': 'counterattack', 'TAPF': 'block',
                    'TAPC': 'received_block', 'M': 'dunk', 'FPF': 'fault', 'FPC': 'received_fault',
                    '+/-': 'plus_minus', 'V': 'efficiency'}

    # Preventing from missing stats
    for key, match in list(header_to_db.items()):
        if key not in header:
            header_to_db.pop(key)

    header_to_db.update({"is_coach": "is_coach",
                         "is_starter": "is_starter",
                         "game": "game",
                         "team": "team",
                         "actor": "actor",
                         "t1_attempt": "t1_attempt",
                         "t2_attempt": "t2_attempt",
                         "t3_attempt": "t3_attempt",
                         "defensive_reb": "defensive_reb",
                         "offensive_reb": "offensive_reb"})

    # The teams dictionary is composed of three subdictionaries, where the first key is the team name,
    # the second key is the number of the player, the third key the stat of the player
    # and the last value the concrete value of the stat.
    stats = defaultdict(dict)
    current_team = None
    for tr in info_players_data('tr').items():
        if tr('.estverde'):  # team information
            if tr.eq(0)('.estverdel'):
                current_team = away_team.name if current_team else home_team.name
                stats[current_team] = defaultdict(dict)
            else:  # omit indexes
                pass
        else:  # players, equipo, total and coach.
            number = None
            for cont, td in enumerate(tr('td').items()):
                if td.text() == "5f" or td.text() == 'Total':  # 5f nor Total are not players.
                    break

                elif cont == 0:  # number of the player
                    number = td.text() if td.text() else 'Equipo'
                    if number in stats[current_team]:
                        raise ValueError('Number {} does already exist!'.format(number))
                    else:
                        stats[current_team][number] = fill_dict(header_to_db.values())
                        stats[current_team][number]['is_starter'] = 1 if td('.gristit') else 0
                        stats[current_team][number]['game'] = game
                        stats[current_team][number]['team'] = home_team if current_team == home_team.name else away_team

                elif cont == 1 and td('a'): # player id
                    href_attribute = td('a').attr('href').split("=")
                    stats[current_team][number]['id'] = href_attribute[-1]
                    is_coach = re.search(r'entrenador', href_attribute[0])
                    stats[current_team][number]['is_coach'] = 1 if is_coach else 0
                    stats[current_team][number]['number'] = None if is_coach else int(number)

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
            stats[team][player].pop('display_name')
            to_insert_many_participants.append(stats[team][player])

    with DATABASE.atomic():
        participants = Participant.insert_many(to_insert_many_participants).execute()
    return participants, actors


def main():
    reset_database()
    year = 2015
    season = Season(year)
    game_number = 1
    with open('../data/'+str(year)+'/'+str(game_number)+'.html') as f:
        raw_game = f.read()

    game, home_team, away_team = get_game_and_teams(raw_game=raw_game, game_number=game_number, season=season)
    referees = get_referees(raw_game=raw_game)
    participants, actors = get_participants_and_actors(raw_game=raw_game, game=game, home_team=home_team, away_team=away_team)

if __name__ == "__main__":
    main()

