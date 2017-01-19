#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from lxml import etree
from collections import deque
from time import sleep
import logging

logger = logging.getLogger(__name__)


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

    def add(self, requests):
        pass

    def addLeft(self, requests):
        pass

    def next(self):
        pass


class DequeScheduler(Scheduler):

    """Docstring for DequeScheduler. """

    def __init__(self):
        """TODO: to be defined1. """
        Scheduler.__init__(self)
        self._requestQueue = deque()

    def add(self, requests):
        self._requestQueue.extend(requests)

    def addLeft(self, requests):
        self._requestQueue.extendleft(requests)

    def next(self):
        try:
            return self._requestQueue.popleft()
        except IndexError:
            return None

    def __str__(self):
        return str(self._requestQueue)


def ConsolePipeline(targetValues):
    for key, value in targetValues.items():
        print(key, value)


class Crawler(object):

    """一个爬虫模块呀."""

    def __init__(self, pageProcessor, domain='', crawlerDelay=0):
        self._pageProcessor = pageProcessor
        self._domain = domain
        self._crawlerDelay = crawlerDelay
        self._requests = []
        self._scheduler = DequeScheduler()
        self._pipelines = []
        self._connectionRetrynum = 0

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
            logger.info('request: %s' % str(request))
            try:
                response = requests.request(method, self._domain + url, **kwargs)
                response.raise_for_status()
            except requests.ConnectionError as e:
                logger.exception(e)
                if self._connectionRetrynum < 5:
                    logger.info('retry(%d): after 30s..........' % self._connectionRetrynum)
                    self._connectionRetrynum += 1
                    self._scheduler.addLeft([request])
            except requests.Timeout as e:
                logger.exception(e)
                logger.info('put in tail of queue')
                self._scheduler.add(request)
            except requests.HTTPError as e:
                logger.exception(e)
                logger.info('put away')
            else:
                self._connectionRetrynum = 0
                tree = etree.HTML(response.text)
                page = Page(tag, url, response, tree)
                # 通过 pageProcessor 提取值和链接
                self._pageProcessor(page)
                # 将目标值输出到 pipeline
                for pipeline in self._pipelines:
                    pipeline(page.getAllValue())
                # 将新链接放到 scheduler
                self._scheduler.add(page.getAllRequests())
            finally:
                request = self._scheduler.next()
                if self._crawlerDelay > 0:
                    logger.info('delay: %d ..........' % self._crawlerDelay)
                    sleep(self._crawlerDelay)
