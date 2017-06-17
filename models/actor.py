import os.path, re, datetime, logging
from pyquery import PyQuery as pq
from src.download import open_or_download, sanity_check
from models.basemodel import BaseModel
from peewee import (PrimaryKeyField, TextField,
                    DoubleField, DateTimeField, BooleanField)


class Actor(BaseModel):

    """
    Class representing an Actor.

    An actor can be either a player or a coach.
    """
    id = PrimaryKeyField()
    acbid = TextField(index=True)
    is_coach = BooleanField(null=True)
    display_name = TextField(index=True, null=True)
    full_name = TextField(null=True)
    nationality = TextField(null=True)
    birthplace = TextField(null=True)
    birthdate = DateTimeField(null=True)
    position = TextField(null=True)
    height = DoubleField(null=True)
    weight = DoubleField(null=True)
    license = TextField(null=True)
    debut_acb = DateTimeField(null=True)
    twitter = TextField(null=True)

    @staticmethod
    def save_actors(logging_level=logging.INFO):
        from src.season import BASE_URL, PLAYERS_PATH, COACHES_PATH
        """
        Method for saving locally the actors.

        :param logging_level: logging object
        """
        logging.basicConfig(level=logging_level)
        logger = logging.getLogger(__name__)

        logger.info('Starting the download of actors...')
        actors = Actor.select()
        for cont, actor in enumerate(actors):
            folder = COACHES_PATH if actor.is_coach else PLAYERS_PATH
            url_tag = 'entrenador' if actor.is_coach else 'jugador'

            filename = os.path.join(folder, actor.acbid + '.html')
            url = os.path.join(BASE_URL, '{}.php?id={}'.format(url_tag, actor.acbid))
            open_or_download(file_path=filename, url=url)

            if cont % (round(len(actors) / 3)) == 0:
                logger.info('{}% already downloaded'.format(round(float(cont) / len(actors) * 100)))

        logger.info('Downloading finished!\n')

    @staticmethod
    def sanity_check(logging_level=logging.INFO):
        from src.season import BASE_URL, PLAYERS_PATH, COACHES_PATH
        sanity_check(PLAYERS_PATH, logging_level)
        sanity_check(COACHES_PATH, logging_level)

    @staticmethod
    def update_content(logging_level=logging.INFO):
        """
        First we insert the instances in the database with basic information and later we update the rest of fields.
        We update the information of the actors that have not been filled yet in the database.
        """
        logging.basicConfig(level=logging_level)
        logger = logging.getLogger(__name__)

        logger.info('Starting to update the actors that have not been filled yet...')
        actors = Actor.select().where(Actor.full_name >> None)
        for cont, actor in enumerate(actors):
            actor._update_content()
            try:
                if len(actors) and cont % (round(len(actors) / 3)) == 0:
                    logger.info( '{}% already updated'.format(round(float(cont) / len(actors) * 100)))
            except ZeroDivisionError:
                pass

        logger.info('Update finished! ({} actors)\n'.format(len(actors)))

    def _update_content(self):
        from src.season import BASE_URL, PLAYERS_PATH, COACHES_PATH
        """
        Update the information of a particular actor.
        """
        folder = COACHES_PATH if self.is_coach else PLAYERS_PATH
        url_tag = 'entrenador' if self.is_coach else 'jugador'

        filename = os.path.join(folder, self.acbid + '.html')
        url = os.path.join(BASE_URL, '{}.php?id={}'.format(url_tag, self.acbid))
        content = open_or_download(file_path=filename, url=url)

        personal_info = self._get_personal_info(content)
        twitter = self._get_twitter(content)
        if twitter:
            personal_info.update({'twitter': twitter})
        Actor.update(**personal_info).where(Actor.acbid == self.acbid).execute()

    def _get_personal_info(self, raw_doc):
        """
        Get personal information about an actor
        :param raw_doc: String
        :return: dict with the info.
        """
        doc = pq(raw_doc)
        personal_info = dict()
        for cont, td in enumerate(doc('.titulojug').items()):
            header = list(map(lambda x: x.strip(), td.text().split("|"))) if "|" in td.text() else [td.text()]
            data = list(map(lambda x: x.strip(), doc('.datojug').eq(cont).text().split("|"))) if td.text() else [td.text()]

            if header[0].startswith("nombre completo"):
                personal_info['full_name'] = data[0]

            elif header[0].startswith("lugar y fecha"):
                try:
                    place, day, month, year = re.search(r'(.*), ([0-9]+)/([0-9]+)/([0-9]+)', data[0]).groups()
                    personal_info['birthplace'] = place.strip()
                    personal_info['birthdate'] = datetime.datetime(year=int(year), month=int(month), day=int(day))
                except:
                    logging.error('The actor {} has an error in the birthdate and birthplace. Msg: {}'.format(personal_info['full_name'], data[0]))

            elif header[0].startswith('posic'):
                for i, field in enumerate(header):
                    if field.startswith('posic'):
                        personal_info['position'] = data[i]
                    elif field.startswith('altura'):
                        personal_info['height'] = data[i].split(" ")[0]
                    elif field.startswith('peso'):
                        personal_info['weight'] = data[i].split(" ")[0]
                    else:
                        raise Exception("Actor's field not found: {}".format(field))

            elif header[0].startswith('nacionalidad'):
                for i, field in enumerate(header):
                    if field.startswith('nacionalidad'):
                        personal_info['nationality'] = data[i]
                    elif field.startswith('licencia'):
                        personal_info['license'] = data[i]
                    else:
                        raise Exception("Actor's field not found: {}".format(field))

            elif header[0].startswith('debut en ACB'):
                day, month, year = re.search(r'([0-9]+)/([0-9]+)/([0-9]+)', data[0]).groups()
                personal_info['debut_acb'] = datetime.datetime(year=int(year), month=int(month), day=int(day))
            else:
                raise Exception('A field of the personal information does not match our patterns: '
                                '{} in {}'.format(td.text(), personal_info['full_name']))

        return personal_info

    def _get_twitter(self, raw_doc):
        """
        Get the twitter of an actor, if it exists.
        :param raw_doc: String
        :return: twitter
        """
        twitter = re.search(r'"http://www.twitter.com/(.*?)"', raw_doc)
        return twitter.groups()[0] if twitter else None
