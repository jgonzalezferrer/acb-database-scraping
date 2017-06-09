import os, re, sys
import datetime
from pyquery import PyQuery as pq
from src.season import Season
from src.models import DATABASE, reset_database, Team, Game, Actor, Participant


def main():
    reset_database()
    year = 2015
    season = Season(year)
    id_game_number = 1
    competition_phase = 'regular'
    round_phase = None

    with open(os.path.join('..', 'data', str(year), 'games', str(id_game_number)+'.html')) as f:
        raw_game = f.read()

    with DATABASE.atomic():
        game = Game.create_instance(raw_game=raw_game, id_game_number=id_game_number,
                                                                     season=season,
                                               competition_phase=competition_phase,
                                                           round_phase=round_phase)


        # referees = get_referees(raw_game=raw_game, game=game)
        Participant.create_instances(raw_game=raw_game, game=game)
        # game.team_home.update_content()

if __name__ == "__main__":
    main()

