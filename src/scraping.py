import os, re, sys
import datetime
from pyquery import PyQuery as pq
from src.season import Season
from src.models import DATABASE, reset_database, Team, Game, Actor, Participant


def scrap_games_and_participants(season):
    with DATABASE.atomic():
        Team.create_instances(season)
        # Regular season
        competition_phase = 'regular'
        round_phase = None
        for id_game_number in range(1, season.get_number_games_regular_season()+1):
            with open(os.path.join('..', 'data', str(season.season), 'games', str(id_game_number)+'.html'), 'r') as f:
                raw_game = f.read()

                game = Game.create_instance(raw_game=raw_game, id_game_number=id_game_number,
                                            season=season,
                                            competition_phase=competition_phase,
                                            round_phase=round_phase)

                Participant.create_instances(raw_game=raw_game, game=game)

        # Playoff
        competition_phase = 'playoff'
        playoff_format = season.get_playoff_format()
        quarter_finals_limit = 4 * playoff_format[0]
        semifinals_limit = quarter_finals_limit + 2 * playoff_format[1]
        for cont, id_game_number in enumerate(range(season.get_number_games_regular_season()+1, season.get_number_games()+1)):
            if cont < quarter_finals_limit:
                round_phase = 'quarter_final'
            elif cont < semifinals_limit:
                round_phase = 'semifinal'
            else:
                round_phase = 'final'

        try:
            with open(os.path.join('..', 'data', str(season.season), 'games', str(id_game_number) + '.html'), 'r') as f:
                raw_game = f.read()

                game = Game.create_instance(raw_game=raw_game, id_game_number=id_game_number,
                                            season=season,
                                            competition_phase=competition_phase,
                                            round_phase=round_phase)

                Participant.create_instances(raw_game=raw_game, game=game)
        except AttributeError:  # some playoff games are missing because they didn't need to play all the games.
            pass


def scrap_actors_and_teams():
    with DATABASE.atomic():
        Actor.save_actors()
        Actor.sanity_check()
        # Actor.update_actors()

def main():
    # reset_database()

    year = 2010
    season = Season(year)


    scrap_games_and_participants(season)
    # scrap_actors_and_teams()







if __name__ == "__main__":
    main()

