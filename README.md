# acb-database-scraping

The aim of this project is to collect information about all the games of the ACB Spanish Basketball League from 1994 to 2016.  A SQLite database has been used for this purpose.

Why from 1994? In 1994, the ACB changed to the current modern league format, which consists of a regular season and a playoff competition between the best 8. 

# Requirements
* Python 3
* pyquery
* peewee

# Instructions on how to execute
The database can be freely accessed from https://data.world/jgonzalezferrer/acb-1994-2016-spanish-basketball-league-results or https://www.kaggle.com/jgonzalezferrer/acb-spanish-basketball-league-results. However, if you want to execute the code by yourself you can just use the `run.py` script:

```
$ python run.py [-r] [-d] [-i] [--start] [first_year] [--end] [last_year]
```

where:

- `-r` indicates whether you want to reset the database.
- `-d`if you want to download locally the games.
- `-i`if you want to inser the information in the database.
- `--start first_year` from which season you want to scrap (1994 by default).
- `--end last_year` until which season you want to scrap (2016 by default).

Therefore, the first time you run the script, you must use `run.py -r -d -i`.

# Content
This dataset includes statistics about the games, teams, players and coaches. It is divided in the following tables:

* **Game**: basic information about the game such as the venue, the attendance, the kickoff, the involved teams and the final score.
* **Participant**: a participant is a player, coach or referee that participates in a game. A participant is associated to a game, an actor and a team. Each row contains information about different stats such as number of points, assists or rebounds.
* **Actor**: an actor represents a player or a coach. It contains personal information about them, such as the height, position or birthday. With this table we can track the different teams that a player has been into.
* **Team**: this class represents a team.
* **TeamName**: the name of a team can change between seasons (and even within the same season). 

In summation, this database contains the stats from games such as http://www.acb.com/fichas/LACB61295.php
