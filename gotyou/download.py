import requests
import os


def get(url, path='.'):
    __get_from_file_url(url, path)


def __get_from_file_url(url, path):
    r = requests.get(url)
    if r.status_code == 200:
        __create_dir_if_not_exists(path)
        path = os.path.join(path, os.path.basename(url))
        with open(path, 'wb') as f:
            f.write(r.content)


def __create_dir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
