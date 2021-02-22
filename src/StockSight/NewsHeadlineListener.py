#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NewsHeadlineListener.py - Base class for new sentiment listener
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import re, asyncio, os
from datetime import datetime
import time
from random import randint


import nltk
from abc import ABC, abstractmethod
from pyppeteer import launch

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

from StockSight.Initializer.ElasticSearch import es
from StockSight.Initializer.Redis import rds
from StockSight.Helper.Sentiment import *
from StockSight.Model.Article import *
from base import Symbol, SymbolAlias, TwitterUser, ArticleAuthor


class NewsHeadlineListener(ABC):
    def __init__(self, news_type, symbol, url=None, use_browser=False):
        self.symbol = Symbol.objects.get(name=symbol)
        self.url = url
        self.type = news_type
        self.cache_length = 2628000
        self.use_browser = use_browser
        self.index_name = config.elasticsearch['table_prefix']['sentiment']+self.symbol.name.lower()

    def execute(self):
        logger.info("Scraping news for %s from %s... Start" % (self.symbol.name, self.type))
        articles = self.get_news_headlines()

        # add any new headlines
        for article_obj in articles:

            if rds.exists(article_obj.msg_id) == 0:

                published_at = article_obj.published_at.isoformat()
                # output news data
                print("\n------------------------------")
                print("Date: " + published_at)
                print("News Headline: " + article_obj.title)
                print("Location (url): " + article_obj.url)

                # create tokens of words in text using nltk
                text_for_tokens = re.sub(
                    r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", article_obj.title)
                tokens = nltk.word_tokenize(text_for_tokens.lower())
                print("NLTK Tokens: " + str(tokens))

                # check ignored tokens from config
                for t in config.sentiment_analyzer['ignore_words']:
                    if t in tokens:
                        logger.info("Text contains token from ignore list, not adding")
                        rds.set(article_obj.msg_id, 1, self.cache_length)
                        continue

                nltk_tokens = self.symbol.symbol_aliases.values_list('name', flat=True)

                # check required tokens from config
                tokenspass = False
                for t in nltk_tokens:
                    if t in tokens:
                        tokenspass = True
                        break

                if not tokenspass:
                    logger.info("Text does not contain token from required list, not adding")
                    rds.set(article_obj.msg_id, 1, self.cache_length)
                    continue

                # get sentiment values
                polarity, subjectivity, sentiment = sentiment_analysis(article_obj.title, True)
                msg_polarity, msg_subjectivity, msg_sentiment = sentiment_analysis(article_obj.body)

                logger.info("Adding news headline to elasticsearch")
                # add news headline data and sentiment info to elasticsearch
                es.index(index=self.index_name,
                         doc_type="_doc",
                         body={
                               "msg_id": article_obj.msg_id,
                               "date": published_at,
                               "referer_url": article_obj.referer_url,
                               "url": article_obj.url,
                               "title": article_obj.title,
                               "message": article_obj.body,
                               "polarity": polarity,
                               "subjectivity": subjectivity,
                               "sentiment": sentiment,
                               "msg_polarity": msg_polarity,
                               "msg_subjectivity": msg_subjectivity,
                               "msg_sentiment": msg_sentiment
                         })

                rds.set(article_obj.msg_id, 1, self.cache_length)

        ArticleAuthor.create_from_articles(articles, self.type)

        logger.info("Scraping news for %s from %s... Done" % (self.symbol.name, self.type))

    @abstractmethod
    def get_news_headlines(self):
        pass

    @abstractmethod
    def get_page_text(self, url):
        pass

    def get_article_with_atag(self, raw_article, parsed_uri):
        a_tag = raw_article.find('a')
        url_link = a_tag.get('href')
        #ignore 3rd party links
        if url_link.find('http') != -1 and url_link.find(parsed_uri) == -1 :
            return None
        return Article(a_tag.text, self.get_proper_new_body_url(url_link,parsed_uri))

    def get_proper_new_body_url(self, article_url, host):
        if article_url.find('http') != -1:
            news_url = article_url
        else:
            news_url = host[0:-1] + article_url
        return news_url

    def can_process(self, article):
        return article is not None and rds.exists(article.msg_id) == 0

    def get_soup(self, url):
        #try not to spam the server, but if you run with 100 stock symbols, it's probably going to spam it anyway lol.
        if(config.spawn_intervals['request_min'] > 0):
            time.sleep(randint(config.spawn_intervals['request_min'], config.spawn_intervals['request_max']))

        html = self.get_text(url)
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def get_text(self, url):
        if self.use_browser:
            return self.browser(url)

        req = requests.get(url)
        return req.text

    def browser(self, url):
        return self.get_or_create_eventloop().run_until_complete(self.__async__browser(url))

    def get_or_create_eventloop(self):
        try:
            return asyncio.get_event_loop()
        except RuntimeError as ex:
            if "There is no current event loop in thread" in str(ex):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return asyncio.get_event_loop()

    async def __async__browser(self, url):
        chrome_bin_path = os.getenv('GOOGLE_CHROME_BIN', '/usr/bin/chromium-browser')
        browser = await launch(options={
            'args': [
                '--no-sandbox',
                # '--proxy-server=103.83.116.202:55443',
                # '--proxy-bypass-list=*',
                # '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox'
                ],
            'executablePath': chrome_bin_path,
            'headless': True
            },
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )
        page = await browser.newPage()
        page.setDefaultNavigationTimeout(60000)
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36')
        await page.goto(url)

        content = await page.evaluate('document.documentElement.innerHTML', force_expr=True)
        await browser.close()

        return content