import os.path

from peewee import (Model, PrimaryKeyField, TextField, IntegerField,
                    DoubleField, DateTimeField, ForeignKeyField, BooleanField,
                    SqliteDatabase, Proxy)
from playhouse.db_url import connect


DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       '..', 'data', 'database.db'))
SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                              'schema.sql'))
DB_PROXY = Proxy()
DATABASE = SqliteDatabase(DB_PATH)
DB_PROXY.initialize(DATABASE)


def initdb(db_url):
    database = connect(db_url)
    DB_PROXY.initialize(database)


def reset_database():
    try:
        DATABASE.close()
    except:
        pass
    try:
        os.remove(DB_PATH)
    except FileNotFoundError:
        pass
    with open(SCHEMA_PATH) as f:
        query = f.read()
    DATABASE.init(DB_PATH)
    DATABASE.connect()
    DATABASE.get_cursor().executescript(query)


class BaseModel(Model):
    class Meta:
        database = DB_PROXY


class Team(BaseModel):
    id = PrimaryKeyField()
    acbid = TextField(unique=True, index=True)
    name = TextField(index=True)
    season = IntegerField()
    alt_names = TextField(null=True)


class Game(BaseModel):
    id = PrimaryKeyField()
    acbid = TextField(unique=True, index=True)
    team_home = ForeignKeyField(Team, related_name='games_home', index=True, null=True)
    team_away = ForeignKeyField(Team, related_name='games_away', index=True, null=True)
    competition_phase = TextField(null=True)
    round = TextField(null=True)
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

    def __str__(self):
        description = "{:<5} {:<7} | {:>20} | ".format("Game", self.acbid, self.competition)
        description += "{} | ".format(self.kickoff_time)
        description += "{} {} - ".format(self.team_home.name, self.score_home)
        description += "{} {}".format(self.score_away, self.team_away.name)
        return description


class Actor(BaseModel):
    id = PrimaryKeyField()
    acbid = TextField(unique=True, index=True)
    display_name = TextField(index=True, null=True)
    first_name = TextField(null=True)
    last_name = TextField(null=True)
    alt_names = TextField(null=True)
    nationality = TextField(null=True)
    birthdate = DateTimeField(null=True)
    position = TextField(null=True)
    height = DoubleField(null=True)
    weight = DoubleField(null=True)


class Participant(BaseModel):
    id = PrimaryKeyField()
    game = ForeignKeyField(Game, related_name='participants', index=True)
    team = ForeignKeyField(Team, index=True, null=True)
    actor = ForeignKeyField(Actor, related_name='participations', index=True, null=True)
    display_name = TextField(null=True)
    number = IntegerField(null=True)
    is_coach = BooleanField(null=True)
    is_referee = BooleanField(null=True)
    is_starter = BooleanField(null=True)
    minutes = IntegerField(null=True)
    point = IntegerField(null=True)
    t2_attempt = IntegerField(null=True)
    t2 = IntegerField(null=True)
    t3_attempt = IntegerField(null=True)
    t3 = IntegerField(null=True)
    t1_attempt = IntegerField(null=True)
    t1 = IntegerField(null=True)
    defensive_reb = IntegerField(null=True)
    offensive_reb = IntegerField(null=True)
    assist = IntegerField(null=True)
    steal = IntegerField(null=True)
    turnover = IntegerField(null=True)
    counterattack = IntegerField(null=True)
    block = IntegerField(null=True)
    received_block = IntegerField(null=True)
    dunk = IntegerField(null=True)
    fault = IntegerField(null=True)
    received_fault = IntegerField(null=True)
    plus_minus = IntegerField(null=True)
    efficiency = IntegerField(null=True)





