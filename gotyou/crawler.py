#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from lxml import etree
from collections import deque
from time import sleep
import logging
import pickle
import os
import sqlite3
import json
import atexit

logger = logging.getLogger(__name__)


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

    def __init__(self):
        self._requestQueue = None

    def add(self, requests):
        pass

    def addLeft(self, requests):
        pass

    def next(self):
        pass

    def recordErrorRequest(self, request):
        pass

    def __str__(self):
        return str(self._requestQueue)


class DequeScheduler(Scheduler):

    """Docstring for DequeScheduler. """

    def __init__(self):
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

    def recordErrorRequest(self, request):
        Scheduler.recordErrorRequest(self, request)


class FileCacheScheduler(Scheduler):

    """Docstring for FileCacheScheduler. """

    def __init__(self, path):
        Scheduler.__init__(self)
        self._path = path
        self._requestQueue = deque()
        self._errorTasks = []
        self._firstTime = True
        atexit.register(self.saveErrorTasks)

    def add(self, requests):
        self._requestQueue.extend(requests)

    def addLeft(self, requests):
        self._requestQueue.extendleft(requests)

    def next(self):
        if self._firstTime:
            self._firstTime = False
            cacheQueue = self.__getQueueFromCache()
            if len(cacheQueue) > 0:
                self._requestQueue = cacheQueue
        self.__cacheQueue()
        try:
            return self._requestQueue.popleft()
        except IndexError:
            return None

    def recordErrorRequest(self, request):
        self._errorTasks.append(request)

    def saveErrorTasks(self):
        self._requestQueue.extend(self._errorTasks)
        self.__cacheQueue()

    def __getCachePath(self):
        return self._path

    def __getQueueFromCache(self):
        path = self.__getCachePath()
        q = None
        if os.path.exists(path):
            with open(path, 'rb') as f:
                q = pickle.load(f)
        if not isinstance(q, deque):
            q = deque()
        return q

    def __cacheQueue(self):
        path = self.__getCachePath()
        cachedir = os.path.dirname(path)
        if cachedir and not os.path.exists(cachedir):
            os.makedirs(cachedir)
        with open(path, 'wb') as f:
            pickle.dump(self._requestQueue, f)


class Pipeline(object):

    """Docstring for Pipeline. """

    def process(page):
        pass


class ConsolePipeline(Pipeline):

    """Docstring for ConsolePipeline. """

    def __init__(self):
        Pipeline.__init__(self)

    def process(self, page: Page):
        for key, value in page.getAllValue().items():
            print(key, value)


class Sqlite3Pipeline(Pipeline):

    """Docstring for Sqlite3Pipelin. """

    def __init__(self, dbPath='crawler.db'):
        Pipeline.__init__(self)
        self._dbPath = dbPath
        self.db = sqlite3.connect(dbPath)
        self.dbcur = self.db.cursor()

    def __del__(self):
        if self.db.in_transaction:
            self.db.commit()

        self.dbcur.close()
        self.db.close()

    def process(self, page):
        if self.db.in_transaction:
            self.db.commit()


class JsonPipeline(Pipeline):

    """Docstring for JsonPipeline. """

    def __init__(self, path):
        Pipeline.__init__(self)

        self._path = path

    def process(self, page):
        dirPath = os.path.join(self._path, page.tag)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        pagePath = os.path.join(dirPath, page.url.replace('/', '_') + '.json')
        with open(pagePath, 'w') as f:
            f.write(json.dumps(page.getAllValue(), ensure_ascii=False, indent=2))


class Crawler(object):

    """一个爬虫模块呀."""

    def __init__(self, pageProcessor, domain='', headers={}, delay=0, timeout=None):
        self._pageProcessor = pageProcessor
        self._domain = domain
        self._delay = delay
        self._timeout = timeout
        self._headers = headers
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
        logger.info('----------start----------')

        self._scheduler.add(self._requests)
        request = self._scheduler.next()

        while request is not None:
            tag, method, url, kwargs = request
            # 添加headers
            if self._headers and 'headers' not in kwargs:
                kwargs['headers'] = self._headers
            if self._timeout and 'timeout' not in kwargs:
                kwargs['timeout'] = self._timeout
            logger.debug('request: %s' % str(request))
            try:
                logger.info('tag: %s, 请求页面: %s' % (tag, self._domain + url))
                response = requests.request(method, self._domain + url, **kwargs)
                response.raise_for_status()
            except requests.ConnectionError as e:
                logger.error(request)
                logger.error(e)
                self._scheduler.recordErrorRequest(request)
                # 等待 30 秒给网络恢复
                sleep(30)
            except requests.Timeout as e:
                logger.error(request)
                logger.error(e)
                self._scheduler.recordErrorRequest(request)
            except requests.HTTPError as e:
                logger.error(request)
                logger.error(e)
                self._scheduler.recordErrorRequest(request)
            else:
                try:
                    tree = etree.HTML(response.text)
                    page = Page(tag, url, response, tree)
                    # 通过 pageProcessor 提取值和链接
                    logger.info('请求成功, 开始分析处理...')
                    self._pageProcessor(page)
                except Exception as e:
                    logger.error(request)
                    logger.exception(e)
                    self._scheduler.recordErrorRequest(request)
                else:
                    # 将目标值输出到 pipeline
                    logger.info('处理完毕，开始输出...')
                    for pipeline in self._pipelines:
                        pipeline.process(page)
                    logger.info('输出完毕, 下一个')
                    # 将新链接放到 scheduler
                    self._scheduler.add(page.getAllRequests())
            finally:
                request = self._scheduler.next()
                if self._delay > 0:
                    logger.info('delay: %d ..........' % self._delay)
                    sleep(self._delay)

        logger.info('----------end----------')


def addRequestToList(l, url, tag, method, **kwargs):
    if isinstance(url, str):
        l.append((tag, method, url, kwargs))
    elif isinstance(url, list):
        l.extend(map(lambda x: (tag, method, x, kwargs), url))
    else:
        raise TypeError('url must be str or list')
