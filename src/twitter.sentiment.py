#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tweet sentiment runner
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import argparse
import sys, time, os
from random import randint

from StockSight.TweetListener import *
from StockSight.EsMap.Sentiment import *
from tweepy import API, Stream, OAuthHandler, TweepError
from base import Symbol, TwitterUser

STOCKSIGHT_VERSION = '0.2'
__version__ = STOCKSIGHT_VERSION


def fetch_status_from_redis(pipe):
    record_added = pipe.get('tweepy:new_record_added')
    pipe.delete('tweepy:new_record_added')
    
    return record_added


# r.transaction(fetch_status_from_redis, *['tweepy:new_record_added'])
if __name__ == '__main__':
    consumer_key = os.getenv('TWITTER_CONSUMER_KEY', config.twitter['consumer_key'])
    consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET', config.twitter['consumer_secret'])
    access_token = os.getenv('TWITTER_ACCESS_TOKEN', config.twitter['access_token'])
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', config.twitter['access_token_secret'])
    

    if not consumer_key or \
       not consumer_secret or \
       not access_token or \
       not access_token_secret:
        logger.error("Invalid Twitter API cred")
        sys.exit(1)

    try:
        # set twitter keys/tokens
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = API(auth)
        # create instance of TweetStreamListener
        TweetStreamListener = TweetStreamListener()
        # create instance of the tweepy stream
        stream = Stream(auth, TweetStreamListener)

        while True:
            for symbol in Symbol.objects.values_list('name', flat=True):
                logger.info('Creating new Elasticsearch index or using existing ' + symbol)
                es.indices.create(index=config.elasticsearch['table_prefix']['sentiment']+symbol.lower(), body=mapping, ignore=[400, 404])


            twitter_feeds = TwitterUser.objects.filter(user_id__isnull=True)
            if len(twitter_feeds) > 0:
                logger.info("Fetching Twitter user ids from Twitter...")
                while True:
                    for twitter_user in twitter_feeds:
                        try:
                            # get user id from screen name using twitter api
                            user = api.get_user(screen_name=twitter_user.username)
                            uid = int(user.id)
                            logger.info("Successfully got %s id: %s..." % (twitter_user.username, uid))
                            twitter_user.user_id=uid
                            twitter_user.save(update_fields=['user_id'])
                            time.sleep(randint(0, 2))
                        except TweepError as te:
                            # sleep a bit in case twitter suspends us
                            logger.warning("Tweepy exception: twitter api error caused by: %s" % te)
                            logger.info("Sleeping for a random amount of time and retrying...")
                            time.sleep(randint(1, 10))
                            continue
                        except KeyboardInterrupt:
                            logger.info("Ctrl-c keyboard interrupt, exiting...")
                            stream.disconnect()
                            sys.exit(0)
                    break

            # search twitter for keywords
            logger.info('NLTK tokens required: ' + str(config.symbols))
            logger.info('NLTK tokens ignored: ' + str(config.sentiment_analyzer['ignore_words']))
            logger.info('Listening for Tweets (ctrl-c to exit)...')

            user_id_list = TwitterUser.objects.values_list('user_id', flat=True)

            if stream.running and False:
                stream.disconnect()
            # elif not stream.running:
            #     stream.filter(follow=user_id_list, languages=['en'], is_async=True)
            # time.sleep()

            if not stream.running:
                stream.filter(follow=user_id_list, languages=['en'], is_async=True)
            
            time.sleep(120)
    except TweepError as te:
        logger.debug("Tweepy Exception: Failed to get tweets caused by: %s" % te)
    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        stream.disconnect()
        sys.exit(0)
    except Exception as e:
        logger.warning("%s" % e)
        pass
