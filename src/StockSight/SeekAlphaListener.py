#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SeekAlphaListener.py - get headline sentiment from SeekingAlpha and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

ISSUE:
SeekingAlpha block frequent access with 403.  Follow_link disabled.

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from StockSight.NewsHeadlineListener import *
import dateparser

class SeekAlphaListener(NewsHeadlineListener):
    def __init__(self, symbol):
        super(SeekAlphaListener, self)\
            .__init__("Seek Alpha", symbol, "https://seekingalpha.com/symbol/%s" % symbol.upper(), True)

    def get_news_headlines(self):

        articles = []

        parsed_uri = urlparse.urljoin(self.url, '/')

        try:
            soup = self.get_soup(self.url)
            # articles_data = soup.select('h3[data-test-id="post-list-item-title"]')
            articles_data = soup.select('article[data-test-id="post-list-item"]')

            if articles_data:
                for raw_article in articles_data:
                    article = self.get_article_with_atag(raw_article.find('h3'), parsed_uri)
                    if self.can_process(article):
                        if config.news['follow_link']:
                            body_url = article.url
                            for p in self.get_page_text(body_url, 'p'):
                                article.body += str(p)+" "

                        author, author_url, publish_date = self.get_metadata(raw_article, parsed_uri)

                        article.published_at = publish_date
                        article.author = author
                        article.author_url = author_url
                        article.referer_url = self.url
                        articles.append(article)

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass

        return articles

    def get_page_text(self, url, selector):
        max_paragraphs = 10
        try:
            soup = self.get_soup(url)
            html_p = soup.findAll(selector)

            if html_p:
                n = 1
                for i in html_p:
                    if n <= max_paragraphs:
                        if i.text is not None:
                            yield i.text
                    else:
                        break
                    n += 1

        except requests.exceptions.RequestException as re:
            logger.warning("Exception: can't crawl web site (%s)" % re)
            pass

    def get_metadata(self, raw_article, parsed_uri):
        # import pdb; pdb.set_trace()
        author_tag = raw_article.select_one('[data-test-id="post-list-author"]')
        date_tag = raw_article.select_one('[data-test-id="post-list-date"]')
        author_link = author_tag.get('href')

        author_url = ''
        if author_link is not None:
            author_url = self.get_proper_new_body_url(author_link, parsed_uri)

        return (
                str(author_tag.text),
                author_url,
                dateparser.parse(date_tag.text)
            )

    def get_page_text(self, url, selector):
        try:
            soup = self.get_soup(url)
            html_p = soup.select(selector)

            if html_p:
                for i in html_p:
                    if i.text is not None:
                        yield i.text
                    else:
                        break

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass

