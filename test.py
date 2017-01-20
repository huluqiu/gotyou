from gotyou.crawler import Crawler, ConsolePipeline, Page, FileCacheScheduler
import yaml
from logging.config import dictConfig
import logging

with open('logconf.yaml') as f:
    logconfig = yaml.load(f)
    dictConfig(logconfig)

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}
logger = logging.getLogger('gotyou')


def pageProcessor(page: Page):
    if page.tag == 'detail':
        page.addTargetValue('title', page.tree.xpath("//*[@id='article_details']//span[@class='link_title']/a/attribute::href"))
    else:
        page.addTargetValue('test', page.tree.xpath("//*[@id='article_list']//span[@class='link_title']/a/text()"))
        page.addRequest(page.tree.xpath("//*[@id='article_list']//span[@class='link_title']/a/attribute::href"), tag='detail', headers=headers)


(Crawler(pageProcessor, 'http://blog.csdn.net/')
        .addRequest('alezaizai', headers=headers)
        .setScheduler(FileCacheScheduler('./'))
        .addPipeline(ConsolePipeline)
        .run())
