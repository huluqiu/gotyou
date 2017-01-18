#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from lxml import etree
from collections import deque


def addRequestToList(l, url, tag=None, method='get', **kwargs):
    if isinstance(url, str):
        l.append((tag, method, url, kwargs))
    elif isinstance(url, list):
        l.extend(map(lambda x: (tag, method, x, kwargs), url))
    else:
        raise TypeError('url must be str or list')


class Page(object):

    """Docstring for Page. """

    def __init__(self, tag, url, response, tree):
        self._targetValues = {}
        self._targetRequests = []
        # 用于标记页面
        self.tag = tag
        # 页面对应的 url
        self.url = url
        # requests 返回的 Response 对象
        self.response = response
        # lxml 的 Element 对象
        self.tree = tree

    def addTargetValue(self, key, value):
        self._targetValues[key] = value

    def getAllValue(self):
        return self._targetValues

    def addRequest(self, url, tag=None, method='get', **kwargs):
        addRequestToList(self._targetRequests, url, tag, method, **kwargs)

    def getAllRequests(self):
        return self._targetRequests


class Scheduler(object):

    """Docstring for Scheduler. """

    def add(url):
        pass

    def next():
        pass


class DequeScheduler(Scheduler):

    """Docstring for DequeScheduler. """

    def __init__(self):
        """TODO: to be defined1. """
        Scheduler.__init__(self)
        self._requestQueue = deque()

    def add(self, requests):
        self._requestQueue.extend(requests)

    def next(self):
        try:
            return self._requestQueue.popleft()
        except IndexError:
            return None


def ConsolePipeline(targetValues):
    for key, value in targetValues.items():
        print(key, value)


class Crawler(object):

    """一个爬虫模块呀."""

    def __init__(self, pageProcessor, domain=''):
        self._pageProcessor = pageProcessor
        self._domain = domain
        self._requests = []
        self._scheduler = DequeScheduler()
        self._pipelines = []

    def addRequest(self, url, tag=None, method='get', **kwargs):
        addRequestToList(self._requests, url, tag, method, **kwargs)
        return self

    def setScheduler(self, scheduler):
        self._scheduler = scheduler
        return self

    def addPipeline(self, pipeline):
        self._pipelines.append(pipeline)
        return self

    def run(self):
        self._scheduler.add(self._requests)
        request = self._scheduler.next()
        while request is not None:
            tag, method, url, kwargs = request
            response = requests.request(method, self._domain + url, **kwargs)
            tree = etree.HTML(response.text)
            page = Page(tag, url, response, tree)
            self._pageProcessor(page)
            for pipeline in self._pipelines:
                pipeline(page.getAllValue())
            self._scheduler.add(page.getAllRequests())
            request = self._scheduler.next()