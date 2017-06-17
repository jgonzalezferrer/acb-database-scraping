import os.path
from pyquery import PyQuery as pq
from peewee import ForeignKeyField
from src.download import open_or_download
from models.basemodel import BaseModel
from src.season import Season
from peewee import (PrimaryKeyField, TextField, IntegerField)


class Team(BaseModel):
    """
    Class representing a Team.

    A team is basically defined by an acb id, and not a name.
    Because the name of a team can change between seasons (and even in a same season).
    """
    id = PrimaryKeyField()
    acbid = TextField(index=True)
    founded_year = IntegerField(null=True)

    @staticmethod
    def create_instances(season):
        """
        Create the database instances of the teams.

        :param season: int
        :return:
        """
        teams_ids = season.get_teams_ids()
        teams_names = []
        for name, acbid in teams_ids.items():
            team = Team.get_or_create(**{'acbid': acbid})[0]
            teams_names.append({'team': team, 'name': name, 'season': season.season})

        TeamName.insert_many(teams_names).on_conflict('IGNORE').execute()

    @staticmethod
    def get_harcoded_teams():
        """
        Extract automatically the ids of the teams based on their names in a game. However, there are some cases
        where the name of the team changes with respect to its official name. Hence, we cannot find an exact coincidence.

        The first decision was to find the closest name in terms of distance similarity. For instance, if the official
        name is 'F.C. BARCELONA' and the name in the match is 'FC BARCELONA' the probability of being the same team is
        high. We track every dismatch observing if they are correct or not.

        In case we find out a wrong match, we hardcode the actual correspondance. Example: The 'C.B CANARIAS' in 2013
        had also the name 'IBEROSTAR TENERIFE'.

        :return: list of harcoded teams
        """
        harcoded_teams = {
            2013: {'CB CANARIAS': 'CAN'},
            2012: {'CAJA LABORAL': 'BAS', 'B&AGRAVE;SQUET MANRESA': 'MAN', 'BÀSQUET MANRESA': 'MAN'},
            2011: {'BIZKAIA BILBAO BASKET': 'BLB'},
            2009: {'VALENCIA BASKET CLUB': 'PAM'}
        }
        return harcoded_teams

    def update_content(self):
        """
        First we insert the instances in the database with basic information and later we update the rest of fields.
        :return:
        """
        season = Season(self.season)

        filename = os.path.join(season.TEAMS_PATH, self.acbid + '.html')
        url = os.path.join(BASE_URL, 'club.php?cod_competicion=LACB&cod_edicion={}&id={}'.format(season.season_id,
                                                                                                 self.acbid))
        content = open_or_download(file_path=filename, url=url)
        self.founded_year = self._get_founded_year(content)
        self.save()

    def _get_founded_year(self, raw_team):
        """
        Extract the founded year of a team.
        :param raw_team: String
        :return: founded year
        """
        doc = pq(raw_team)

        if doc('.titulojug').eq(0).text().startswith('Año de fundac'):
            return int(doc('.datojug').eq(0).text())
        else:
            raise Exception('The first field is not the founded year.')


class TeamName(BaseModel):
    """
    Class representing a TeamName.

    The name of a team depends on the season. And even within a season can have several names.
    """
    id = PrimaryKeyField()
    team = ForeignKeyField(Team, related_name='names', index=True)
    name = TextField()
    season = IntegerField()

    class Meta:
        indexes = (
            (('name', 'season'), True),
        )

    @staticmethod
    def create_instance(team_name, acbid, season):
        """
        Create an instance of a TeamName

        :param team_name: String
        :param acbid: String
        :param season: int
        """
        team = Team.get(Team.acbid == acbid)
        TeamName.get_or_create(**{'name': team_name, 'team': team, 'season': season})

    @staticmethod
    def create_harcoded_teams():
        """
        The season 2004 doesn't provide a standing page to extract the ids of the teams. We have tried to reused
        previous teams' name but there are a few that are not in the database.
        :return:
        """
        TeamName.create_instance('BREOGÁN LUGO', 'BRE', 2004)
        TeamName.create_instance('C. BALONCESTO MURCIA', 'MUR', 2004)
        TeamName.create_instance('ESTUDIANTES CAJA POSTAL', 'EST', 2004)
        TeamName.create_instance('COREN ORENSE', 'ORE', 2004)
        TeamName.create_instance('SOMONTANO HUESCA', 'HUE', 2004)
        TeamName.create_instance('7UP JOVENTUT', 'JOV', 2004)
