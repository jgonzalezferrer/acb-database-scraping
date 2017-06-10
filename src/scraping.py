import os, re, sys
import datetime
from pyquery import PyQuery as pq
from src.season import Season
from src.models import DATABASE, reset_database, Team, Game, Actor, Participant


def main():
    reset_database()
    year = 2015
    season = Season(year)
    competition_phase = 'regular'
    round_phase = None

    # season.save_games()
    with DATABASE.atomic():
        for id_game_number in range(1, season.get_number_games_regular_season()+1):
            with open(os.path.join('..', 'data', str(year), 'games', str(id_game_number)+'.html'), 'r') as f:
                raw_game = f.read()

                game = Game.create_instance(raw_game=raw_game, id_game_number=id_game_number,
                                            season=season,
                                            competition_phase=competition_phase,
                                            round_phase=round_phase)

                Participant.create_instances(raw_game=raw_game, game=game)



        #Actor.get((Actor.acbid=='1LC') & (Actor.is_coach==0)).update_content()
        # Actor.get((Actor.acbid=='ADD') & (Actor.is_coach==1)).update_content()

        # game.team_home.update_content()

if __name__ == "__main__":
    main()

