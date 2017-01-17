from gotyou import Crawler

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}


def pageProcessor(page):
    if page.tag is 'detail':
        page.addTargetValue('detail', 'haha')
        print(page.response)
    else:
        page.addTargetValue('test', page.tree.xpath("//*[@id='article_list']//span[@class='link_title']/a/text()"))
        page.addRequest(page.tree.xpath("//*[@id='article_list']//span[@class='link_title']/a/attribute::href"), tag='detail', headers=headers)


(Crawler(pageProcessor, 'http://blog.csdn.net/')
        .addRequest('alezaizai', headers=headers)
        .run())
