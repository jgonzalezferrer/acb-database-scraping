import urllib.request, os


def get_page(url):
    """Get data from URL"""
    return urllib.request.urlopen(url).read().decode('utf-8')


def save_content(file_path, content):
    """Saves the content to a file in the path provided"""
    with open(file_path, 'w') as file:
        file.write(content)
        return content


def open_or_download(file_path, url):
    """Open or download a file"""
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    else:
        html_file = get_page(url)
        return save_content(file_path, html_file)


def validate_dir(folder):
    """Creates a directory if it doesn't already exist."""
    if not os.path.exists(folder):
        os.mkdir(folder)