import urllib.request, os, logging
from pyquery import PyQuery as pq

def get_page(url):
    """
    Get data from URL.

    :param url: String
    :return: content of the page
    """
    return urllib.request.urlopen(url).read().decode('utf-8')


def save_content(file_path, content):
    """
    Saves the content to a file in the path provided.

    :param file_path: String
    :param content: String
    :return: content of the page
    """
    with open(file_path, 'w') as file:
        file.write(content)
        return content


def open_or_download(file_path, url):
    """
    Open or download a file.

    :param file_path: String
    :param url: String
    :return: content of the file.
    """
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    else:
        html_file = get_page(url)
        return save_content(file_path, html_file)


def validate_dir(folder):
    """
    Creates a directory if it doesn't already exist.

    :param folder: String
    """
    if not os.path.exists(folder):
        os.mkdir(folder)


def sanity_check(directory_name, logging_level=logging.INFO):
    """
    Checks if thes file within a directoy have been correctly downloaded

    :param directory_name: String
    :param logging_level: logging object
    """
    logging.basicConfig(level=logging_level)
    logger = logging.getLogger(__name__)

    errors = []
    directory = os.fsencode(directory_name)
    for file in os.listdir(directory):
        with open(os.path.join(directory, file)) as f:
            raw_html = f.read()

            doc = pq(raw_html)
            if doc("title").text() == '404 Not Found':
                errors.append(os.fsdecode(file))

    if errors: raise Exception('There are {} errors in the downloads!'.format(len(errors)))
    logger.info('Sanity check of {} correctly finished!\n'.format(os.fsdecode(directory)))
    return errors