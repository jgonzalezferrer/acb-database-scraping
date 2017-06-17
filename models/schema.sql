CREATE TABLE team (
    id INTEGER PRIMARY KEY,  -- SQLite automatically increments PKs.
    acbid TEXT UNIQUE NOT NULL,  -- Soccerway team ID.
    founded_year INTEGER
);
CREATE INDEX team_acbid_idx ON team(acbid);

CREATE TABLE teamName (
    id INTEGER PRIMARY KEY,
    team_id INTEGER REFERENCES team,
    name TEXT NOT NULL,
    season INTEGER NOT NULL,
    UNIQUE (name, season)
);
CREATE INDEX teamName_team_id_idx ON teamName(team_id);

CREATE TABLE game (
    id INTEGER PRIMARY KEY,  -- SQLite automatically increments PKs.
    acbid TEXT UNIQUE NOT NULL,  -- ACB game ID.
    team_home_id INTEGER REFERENCES team,
    team_away_id INTEGER REFERENCES team,

    -- Regular season or playoff.
    competition_phase TEXT,

    -- If playoff, round of the game (quarter final, semifinal, final).
    round_phase TEXT,

    -- Number of the journey. In regular season it is generally one journey per week. In playoff it is one journey per round match.
    journey INTEGER,

    venue TEXT,
    attendance INTEGER,

    -- Kick-off time. In number of seconds since UNIX epoch, UTC timezone.
    kickoff_time TIMESTAMP,

    -- Final score including extra time.
    score_home INTEGER,
    score_away INTEGER,

    -- Score in first quarter.
    score_home_first INTEGER,
    score_away_first INTEGER,

    -- Score in second quarter.
    score_home_second INTEGER,
    score_away_second INTEGER,

    -- Score in third quarter.
    score_home_third INTEGER,
    score_away_third INTEGER,

    -- Score in fourth quarter.
    score_home_fourth INTEGER,
    score_away_fourth INTEGER,

    -- Score in extra-time. Possibly NULL.
    score_home_extra INTEGER,
    score_away_extra INTEGER,

    -- True flag if all the information with respect to the game has been inserted correctly.
    db_flag BOOLEAN
);
CREATE INDEX game_acbid_idx ON game(acbid);
CREATE INDEX game_team_home_id_idx ON game(team_home_id);
CREATE INDEX game_team_away_id_idx ON game(team_away_id);
CREATE INDEX game_kickoff_time_idx ON game(kickoff_time);


/* An actor is a player or a coach. In this table, many fields may be set to
 * NULL. */
CREATE TABLE actor (
    id INTEGER PRIMARY KEY,  -- SQLite automatically increments PKs.
    acbid TEXT NOT NULL,  -- ACB player / coach ID.
    is_coach BOOLEAN,
    display_name TEXT,
    full_name TEXT,
    nationality TEXT,
    birthplace TEXT,
    -- Date of birth. In number of seconds since UNIX epoch, UTC timezone.
    birthdate TIMESTAMP,
    position TEXT,  -- simple string
    height REAL,  -- In meters.
    weight REAL,  -- In kilograms.
    license TEXT,
    debut_acb TIMESTAMP,
    twitter TEXT
);
CREATE INDEX actor_acbd_idx ON actor(acbid);
CREATE INDEX actor_display_name_idx ON actor(display_name);


/* A participant is a player, a coach or a referee. In this table, many fields may be set to
 * NULL. */
CREATE TABLE participant (
    id INTEGER PRIMARY KEY,  -- SQLite automatically increments PKs.
    game_id INTEGER REFERENCES game NOT NULL,
    team_id INTEGER REFERENCES team,
    actor_id INTEGER REFERENCES actor,

    -- Display name of the actor
    display_name TEXT,

    -- First name of the actor
    first_name TEXT,

    -- Last name of the actor
    last_name TEXT,

    -- Squad number of the player
    number INTEGER,

    -- True if the actor is the coach.
    is_coach BOOLEAN,

    -- True if the actor is a referee.
    is_referee BOOLEAN,

    -- True if the player starts the game.
    is_starter BOOLEAN,

     -- Number of minutes played.
    minutes INTEGER,

    point INTEGER,

    -- Two points attempts and scored.
    t2_attempt INTEGER,
    t2 INTEGER,

    -- Three points attempts and scored.
    t3_attempt INTEGER,
    t3 INTEGER,

     -- Free shots attempts and scored.
    t1_attempt INTEGER,
    t1 INTEGER,

    -- Offensive and deffensive rebounds
    defensive_reb INTEGER,
    offensive_reb INTEGER,

    -- Assist
    assist INTEGER,

    -- Steals and turnovers
    steal INTEGER,
    turnover INTEGER,

    -- Counterattacks
    counterattack INTEGER,

    --  Blocks and received blocks
    block INTEGER,
    received_block INTEGER,

    -- Dunks
    dunk INTEGER,

    -- Faults and received faults
    fault INTEGER,
    received_fault INTEGER,

    -- +/- ratio. NULL for old matches.
    plus_minus INTEGER,

    -- Efficiency.
    efficiency INTEGER

);
CREATE INDEX participant_game_id_idx ON participant(game_id);
CREATE INDEX participant_team_id_idx ON participant(team_id);
CREATE INDEX participant_actor_id_idx ON participant(actor_id);




