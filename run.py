import argparse, os, re
from models.basemodel import DATABASE, reset_database
from models.game import Game
from models.team import TeamName, Team
from models.actor import Actor
from models.participant import Participant
from src.season import Season


def download_games(season):
    """
    Download locally the games of a certain season
    :param season: Season object.
    """
    Game.save_games(season)
    Game.sanity_check(season)


def insert_games(season):
    """
    Extract and insert the information regarding the games of a season.
    :param season: Season object.
    """
    if season.season == 1994:  # the 1994 season doesn't have standing page.
        TeamName.create_harcoded_teams()

    with DATABASE.atomic():
        # Create the instances of Team.
        Team.create_instances(season)

        # Regular season
        competition_phase = 'regular'
        round_phase = None
        for id_game_number in range(1, season.get_number_games_regular_season() + 1):
            with open(os.path.join('..', 'data', str(season.season), 'games', str(id_game_number) + '.html'),
                      'r') as f:
                raw_game = f.read()

                game = Game.create_instance(raw_game=raw_game, id_game_number=id_game_number,
                                            season=season,
                                            competition_phase=competition_phase,
                                            round_phase=round_phase)

                Participant.create_instances(raw_game=raw_game, game=game)

        # Playoff
        competition_phase = 'playoff'
        round_phase = None
        playoff_format = season.get_playoff_format()
        quarter_finals_limit = 4 * playoff_format[0]
        semifinals_limit = quarter_finals_limit + 2 * playoff_format[1]

        relegation_teams = season.get_relegation_teams()  # in some seasons there was a relegation playoff.
        cont = 0
        id_game_number = season.get_number_games_regular_season()
        playoff_end = season.get_number_games()

        while id_game_number < playoff_end:
            id_game_number += 1
            with open(os.path.join('..', 'data', str(season.season), 'games', str(id_game_number) + '.html'),
                      'r') as f:
                raw_game = f.read()

                # A playoff game might be blank if the series ends before the last game.
                if re.search(r'<title>ACB.COM</title>', raw_game) \
                        and (re.search(r'"estverdel"> <', raw_game)
                             or re.search(r'<font style="font-size : 12pt;">0 |', raw_game)):
                    cont += 1
                    continue

                game = Game.create_instance(raw_game=raw_game, id_game_number=id_game_number,
                                            season=season,
                                            competition_phase=competition_phase,
                                            round_phase=round_phase)

                home_team_name = TeamName.get(
                    (TeamName.team == game.team_home) & (TeamName.season == season.season)).name
                away_team_name = TeamName.get(
                    (TeamName.team == game.team_away) & (TeamName.season == season.season)).name

                if (home_team_name or away_team_name) in relegation_teams:
                    game.competition_phase = 'relegation_playoff'
                else:
                    if cont < quarter_finals_limit:
                        game.round_phase = 'quarter_final'
                    elif cont < semifinals_limit:
                        game.round_phase = 'semifinal'
                    else:
                        game.round_phase = 'final'
                    cont += 1

                game.save()

                # Create the instances of Participant
                Participant.create_instances(raw_game=raw_game, game=game)


def update_games():
    """
    Update the information about teams and actors and correct errors.
    """
    # Download actor's page.
    Actor.save_actors()
    Actor.sanity_check()

    with DATABASE.atomic():
        Team.update_content()
        Participant.fix_participants()  # there were a few errors in acb. Manually fix them.
        Actor.update_content()


def main(args):
    if args.r:  # reset the database.
        reset_database()

    first_season = args.first_season
    last_season = args.last_season+1

    if args.d:  # download the games.
        for year in reversed(range(first_season, last_season)):
            season = Season(year)
            download_games(season)

    if args.i:
        # Extract and insert the information in the database.
        for year in reversed(range(first_season, last_season)):
            season = Season(year)
            insert_games(season)

        # Update missing info about actors, teams and participants.
        update_games()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", action='store_true', default=False)
    parser.add_argument("-d", action='store_true', default=False)
    parser.add_argument("-i", action='store_true', default=False)
    parser.add_argument("--start", action='store', dest="first_season", default=1994, type=int)
    parser.add_argument("--end", action='store', dest="last_season", default=2016, type=int)

    main(parser.parse_args())