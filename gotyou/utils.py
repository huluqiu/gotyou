import json
import requests
from lxml import etree
from collections import deque
import pickle
import os


def jsonload(path):
    r = {}
    with open(path, 'r') as f:
        r = json.load(f)
    return r


def jsondump(obj, path):
    __makedirs_ifneed(path)
    with open(path, 'w') as f:
        json.dump(obj, f)


def tree(url, **kwargs):
    r = requests.get(url, **kwargs)
    return etree.HTML(r.text)


def get_cache_queue(path):
    q = deque()
    with open(path, 'rb') as f:
        q = pickle.load(f)
    return q


def cache_queue(q, path):
    __makedirs_ifneed(path)
    with open(path, 'wb') as f:
        pickle.dump(q, f)


def __makedirs_ifneed(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
