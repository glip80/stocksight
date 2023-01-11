# https://github.com/LLukas22/Finance-Data-Scraper
import logging
import hashlib
import requests
import time
import random
import pytz
import datetime
from dateutil.parser import parse
from bs4 import BeautifulSoup
import pandas as pd

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0'


class News_Item(object):
    def __init__(self, tickers: list[str], pub_date: datetime, title: str, publisher: str, link: str) -> None:
        self.publisher = publisher.upper()
        self.link = link
        self.pub_date = pub_date
        self.tickers = tickers
        self.__hash = None

    @property
    def hash(self) -> str:
        if self.__hash:
            return self.__hash
        else:
            self.__hash = hashlib.sha512((self.link).encode("UTF-8")).hexdigest()
            return self.__hash


class NewsScrapper:

    def __init__(self, logger, args):
        self.args = args
        self.logger = logger

    def get_finviz_news_items(self, tickers: list[str]):  # -> list[News_Item]:
        news_items = []
        finwiz_url = 'https://finviz.com/quote.ashx?t='
        for ticker in tickers:
            try:
                time.sleep(random.uniform(0.5, 1.0))  # try to avoid being rate limited
                url = finwiz_url + ticker.lower()
                result = requests.get(url, headers={'User-Agent': USER_AGENT})
                if result.status_code == 200:
                    html = BeautifulSoup(result.content, features='html.parser')
                    news_table = html.find(id='news-table')

                    for x in news_table.findAll('tr'):
                        title = x.a.text
                        link = x.a.attrs['href']
                        publisher = x.span.get_text().strip()

                        date_scrape = x.td.text.split()
                        datetime = parse(" ".join(date_scrape)).astimezone(pytz.UTC)
                        news_items.append([ticker, datetime, title, publisher, link])  # News_Item
            except Exception as e:
                logging.error(e)
        return pd.DataFrame(news_items, columns=[['ticker', 'datetime', 'title', 'publisher', 'link']])


#
# tickers = ['NVDA']
# newsapi = NewsScrapper(None, None)
# news = newsapi.get_finviz_news_items(tickers)
# news.to_csv('NVDA.csv')
# print(df)
# for index, row in df.iterrows():
#     print(index)
