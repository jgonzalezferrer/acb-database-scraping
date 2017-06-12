import os, re, sys
import datetime
from pyquery import PyQuery as pq
from src.season import Season
from src.models import DATABASE, reset_database, Team, TeamName, Game, Actor, Participant


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
        round_phase = None
        playoff_format = season.get_playoff_format()
        quarter_finals_limit = 4 * playoff_format[0]
        semifinals_limit = quarter_finals_limit + 2 * playoff_format[1]

        relegation_teams = season.get_relegation_teams()
        cont = 0
        id_game_number = season.get_number_games_regular_season()+1
        playoff_end = season.get_number_games()

        while id_game_number <= playoff_end:
            with open(os.path.join('..', 'data', str(season.season), 'games', str(id_game_number) + '.html'), 'r') as f:
                print(id_game_number, playoff_end)
                id_game_number += 1
                raw_game = f.read()

                if re.search(r'<title>ACB.COM</title>', raw_game) \
                        and (re.search(r'"estverdel"> <', raw_game)
                             or re.search(r'<font style="font-size : 12pt;">0 |', raw_game)):
                    cont += 1
                    continue

                game = Game.create_instance(raw_game=raw_game, id_game_number=id_game_number,
                                            season=season,
                                            competition_phase=competition_phase,
                                            round_phase=round_phase)

                home_team_name = TeamName.get((TeamName.team == game.team_home) & (TeamName.season == season.season)).name
                away_team_name = TeamName.get((TeamName.team == game.team_away) & (TeamName.season == season.season)).name
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
                Participant.create_instances(raw_game=raw_game, game=game)

def scrap_actors_and_teams():
    with DATABASE.atomic():
        Actor.save_actors()
        Actor.sanity_check()
        # esteban = Actor.get(Actor.display_name=='Esteban, Màxim')
        # esteban.acbid = '2CH'
        # esteban.save()
        #
        # esteban = Actor.get(Actor.display_name == 'Sharabidze, G.')
        # esteban.acbid = 'Y9G'
        # esteban.save()
        #
        # real_tavares = Actor.get((Actor.display_name == 'Tavares, W.') & (Actor.acbid == 'T2Z'))
        #
        # try:
        #     fake_tavares = Actor.get((Actor.display_name == 'Tavares, W.') & (Actor.acbid == 'SHP'))
        #
        #     for participation in fake_tavares.participations:
        #         participation.actor = real_tavares
        #         participation.save()
        #     fake_tavares.delete_instance()
        # except Actor.DoesNotExist:
        #     pass
        #
        # real_stobart = Actor.get((Actor.display_name == 'Stobart, Micky') & (Actor.acbid == 'B7P'))
        #
        # try:
        #     fake_stobart = Actor.get((Actor.display_name == 'Stobart, Micky') & (Actor.acbid == 'FII'))
        #
        #     for participation in fake_stobart.participations:
        #         participation.actor = real_stobart
        #         participation.save()
        #         fake_stobart.delete_instance()
        # except Actor.DoesNotExist:
        #     pass
        #
        # real_stobart = Actor.get((Actor.display_name == 'Olaizola, Julen') & (Actor.acbid == 'T86'))
        #
        # try:
        #     fake_stobart = Actor.get((Actor.display_name == 'Olaizola, Julen') & (Actor.acbid == '162'))
        #
        #     for participation in fake_stobart.participations:
        #         participation.actor = real_stobart
        #         participation.save()
        #         fake_stobart.delete_instance()
        # except Actor.DoesNotExist:
        #     pass
        #
        # real_stobart = Actor.get((Actor.display_name == 'Izquierdo, Antonio') & (Actor.acbid == '773'))
        #
        # try:
        #     fake_stobart = Actor.get((Actor.display_name == 'Izquierdo, Antonio') & (Actor.acbid == 'YHK'))
        #
        #     for participation in fake_stobart.participations:
        #         participation.actor = real_stobart
        #         participation.save()
        #         fake_stobart.delete_instance()
        # except Actor.DoesNotExist:
        #     pass
        #
        Actor.update_actors()


def main():
        reset_database()
    # for year in reversed(range(1998, 2016)):
        year = 1998
        season = Season(year)
        Game.save_games(season)
        Game.sanity_check(season)
        scrap_games_and_participants(season)
        # scrap_actors_and_teams()

if __name__ == "__main__":
    main()

