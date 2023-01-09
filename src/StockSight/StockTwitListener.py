
import re, nltk
# import requests

from pystocktwits import Streamer


from StockSight.Helper.Sentiment import *
from StockSight.Initializer.ConfigReader import *
from StockSight.Initializer.Logger import logger
from StockSight.Initializer.ElasticSearch import es
from StockSight.Initializer.Redis import rds
from base import Symbol, SymbolAlias, TwitterUser


regex = re

class StockTwitListener(object):
    def __init__(self, symbol):
        self.index_name = None
        self.symbol = Symbol.objects.get(name=symbol)
        self.twit = Streamer()

    def get_chatter(self):
        symbol = self.symbol.name
        logger.info("Scraping price for %s from StockTwit ..." % symbol)

        if self.index_name is None:
            self.index_name = config.elasticsearch['table_prefix']['price']+symbol.lower()

        # url = "https://api.stocktwits.com/api/2/streams/symbol/SYMBOL.json"

        logger.info("Grabbing stock data for symbol %s..." % symbol)

        try:
            call_id_key = 'stocktwit:'+str(symbol)
            # , since=0, max=0, limit=0, callback=None, filter=None
            since = rds.get(call_id_key)
            data = self.twit.get_symbol_msgs(symbol, since=since, limit=30)
            # add stock symbol to url
            # url = regex.sub("SYMBOL", symbol, url)
            # get stock data (json) from url
            # try:
            #     r = requests.get(url)
            #     data = r.json()
            # except (requests.HTTPError, requests.ConnectionError, requests.ConnectTimeout) as re:
            #     logger.error("Exception: exception getting stock data from url caused by %s" % re)
            #     raise
            call_id = data.get('cursor', {}).get('since')
            
            messages = data['messages']

            for message in messages:
                text = message['body']

                # clean up tweet text more
                text = text.replace("\n", " ")
                text = re.sub(r"http\S+", "", text)
                text = re.sub(r"&.*?;", "", text)
                text = re.sub(r"<.*?>", "", text)
                # text = text.replace("RT", "")
                text = text.replace(u"…", "")
                text = text.strip()

                created_at = message.get('created_at')
                user_name = message.get('user', {}).get('username')
                name = message.get('user', {}).get('name')
                followers = message.get('user', {}).get('followers')
                following = message.get('user', {}).get('following')
                watchlist_stocks_count = message.get('user', {}).get('watchlist_stocks_count')
                ideas_count = message.get('user', {}).get('ideas')
                twit_id = message.get('id')
                text_raw = message.get('body')
                text_filtered = str(text)

                # output twitter data
                print("\n------------------------------")
                print("Twit Date: " + created_at)
                print("User Name: " + user_name)
                # print("Location: " + location)
                # print("Language: " + language)
                print("Following: " + str(following))
                print("Followers: " + str(followers))
                print("Watchlist Stocks Count: " + str(watchlist_stocks_count))
                print("Twit ID: " + str(twit_id))
                print("Twit Raw Text: " + text_raw)
                print("Twit Filtered Text: " + text_filtered)

                # create tokens of words in text using nltk
                text_for_tokens = re.sub(
                    r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", text_filtered)
                tokens = nltk.word_tokenize(text_for_tokens)
                print("NLTK Tokens: " + str(tokens))

                # do some checks before adding to elasticsearch and crawling urls in tweet
                # if friends == 0 or \
                # followers < config.twitter['min_followers'] or \
                # statuses == 0 or \
                # text == "":
                #     logger.info("Tweet doesn't meet min requirements, not adding")
                #     return True

                redis_id = 'stocktwit'+str(twit_id)
                should_halt_processing=False

                if rds.exists(redis_id):
                    logger.info("Twit already exists")
                    should_halt_processing=True


                if should_halt_processing:
                    continue
                                # check ignored tokens from config
                for t in config.sentiment_analyzer['ignore_words']:
                    if t in tokens:
                        logger.info("Twit contains token from ignore list, not adding")
                        should_halt_processing=True
                        break

                if should_halt_processing:
                    continue

                    # strip out hashtags for language processing
                msg = re.sub(r"[#|@|\$]\S+", "", text)
                msg.strip()

                # get sentiment values
                polarity, subjectivity, sentiment = sentiment_analysis(msg)

                self.index_name = config.elasticsearch['table_prefix']['sentiment']+symbol.lower()
                logger.info("Adding twit to elasticsearch")
                # add twitter data and sentiment info to elasticsearch
                es.index(index=self.index_name,
                        doc_type="_doc",
                        body={
                            "msg_id": redis_id,
                            "author": user_name,
                            # "location": location,
                            "date": created_at,
                            "title": text_filtered,
                            "message": '',
                            "polarity": polarity,
                            "subjectivity": subjectivity,
                            "sentiment": sentiment
                        })

                # add tweet_id to cache
                rds.set(redis_id, 1, 86400)

                # return True

            rds.set(call_id_key, call_id, 86400)
        except Exception as e:
            logger.warning("Exception: exception caused by: %s" % e)
            raise
#                         created_at
# user_name
# name
# followers
# following
# watchlist_stocks_count
# ideas_count
# twit_id
# text_raw
# text_filtered