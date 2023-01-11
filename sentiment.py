#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sentiment.py - analyze tweets on Twitter and add
relevant tweets and their sentiment values to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2020
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import sys
import time
import re
import requests
import argparse
import logging

from news_headline import NewsHeadlineListener
# from tweeter_posts import TweetStreamingClient, get_twitter_users_from_url, get_twitter_users_from_file

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
from tweepy import StreamRule, Client, TweepyException
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from random import randint, randrange
# import elasticsearch host, twitter keys and tokens
from config import *


STOCKSIGHT_VERSION = '0.1-b.12'
__version__ = STOCKSIGHT_VERSION

IS_PY3 = sys.version_info >= (3, 0)

if not IS_PY3:
    print("Sorry, stocksight requires Python 3.")
    sys.exit(1)




# file to hold twitter user ids
twitter_users_file = './twitteruserids.txt'

prev_time = time.time()
sentiment_avg = [0.0,0.0,0.0]


def clean_text(text):
    # clean up text
    text = text.replace("\n", " ")
    text = re.sub(r"https?\S+", "", text)
    text = re.sub(r"&.*?;", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("RT", "")
    text = text.replace(u"…", "")
    text = text.strip()
    return text


if __name__ == '__main__':
    # parse cli args
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", metavar="INDEX", default="stocksight",
                        help="Index name for Elasticsearch (default: stocksight)")
    parser.add_argument("-d", "--delindex", action="store_true",
                        help="Delete existing Elasticsearch index first")
    parser.add_argument("-s", "--symbol", metavar="SYMBOL", required=True,
                        help="Stock symbol you are interesed in searching for, example: TSLA")
    parser.add_argument("-k", "--keywords", metavar="KEYWORDS",
                        help="Use keywords to search for in Tweets instead of feeds. "
                             "Separated by comma, case insensitive, spaces are ANDs commas are ORs. "
                             "Example: TSLA,'Elon Musk',Musk,Tesla,SpaceX")
    parser.add_argument("-a", "--addtokens", action="store_true",
                        help="Add nltk tokens required from config to keywords")
    parser.add_argument("-u", "--url", metavar="URL",
                        help="Use twitter users from any links in web page at url")
    parser.add_argument("-f", "--file", metavar="FILE",
                        help="Use twitter user ids from file")
    parser.add_argument("-l", "--linksentiment", action="store_true",
                        help="Follow any link url in tweets and analyze sentiment on web page")
    parser.add_argument("-n", "--newsheadlines", action="store_true",
                        help="Get news headlines instead of Twitter using stock symbol from -s")
    parser.add_argument("--frequency", metavar="FREQUENCY", default=120, type=int,
                        help="How often in seconds to retrieve news headlines (default: 120 sec)")
    parser.add_argument("--followlinks", action="store_true",
                        help="Follow links on news headlines and scrape relevant text from landing page")
    parser.add_argument("-w", "--websentiment", action="store_true",
                        help="Get sentiment results from text processing website")
    parser.add_argument("--overridetokensreq", metavar="TOKEN", nargs="+",
                        help="Override nltk required tokens from config, separate with space")
    parser.add_argument("--overridetokensignore", metavar="TOKEN", nargs="+",
                        help="Override nltk ignore tokens from config, separate with space")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Increase output verbosity")
    parser.add_argument("--debug", action="store_true",
                        help="Debug message output")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Run quiet with no message output")
    parser.add_argument("-V", "--version", action="version",
                        version="stocksight v%s" % STOCKSIGHT_VERSION,
                        help="Prints version and exits")
    args = parser.parse_args()

    # set up logging
    logger = logging.getLogger('stocksight')
    logger.setLevel(logging.INFO)
    eslogger = logging.getLogger('elasticsearch')
    eslogger.setLevel(logging.WARNING)
    tweepylogger = logging.getLogger('tweepy')
    tweepylogger.setLevel(logging.INFO)
    requestslogger = logging.getLogger('requests')
    requestslogger.setLevel(logging.INFO)
    logging.addLevelName(
        logging.INFO, "\033[1;32m%s\033[1;0m"
                      % logging.getLevelName(logging.INFO))
    logging.addLevelName(
        logging.WARNING, "\033[1;31m%s\033[1;0m"
                         % logging.getLevelName(logging.WARNING))
    logging.addLevelName(
        logging.ERROR, "\033[1;41m%s\033[1;0m"
                       % logging.getLevelName(logging.ERROR))
    logging.addLevelName(
        logging.DEBUG, "\033[1;33m%s\033[1;0m"
                       % logging.getLevelName(logging.DEBUG))
    logformatter = '%(asctime)s [%(levelname)s][%(name)s] %(message)s'
    loglevel = logging.INFO
    logging.basicConfig(format=logformatter, level=loglevel)
    if args.verbose:
        logger.setLevel(logging.INFO)
        eslogger.setLevel(logging.INFO)
        tweepylogger.setLevel(logging.INFO)
        requestslogger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        eslogger.setLevel(logging.DEBUG)
        tweepylogger.setLevel(logging.DEBUG)
        requestslogger.setLevel(logging.DEBUG)
    if args.quiet:
        logger.disabled = True
        eslogger.disabled = True
        tweepylogger.disabled = True
        requestslogger.disabled = True

    # print banner
    if not args.quiet:
        c = randint(1, 4)
        if c == 1:
            color = '31m'
        elif c == 2:
            color = '32m'
        elif c == 3:
            color = '33m'
        elif c == 4:
            color = '35m'

        banner = """\033[%s
       _                     _                 
     _| |_ _           _   _| |_ _     _   _   
    |   __| |_ ___ ___| |_|   __|_|___| |_| |_ 
    |__   |  _| . |  _| '_|__   | | . |   |  _|
    |_   _|_| |___|___|_,_|_   _|_|_  |_|_|_|  
      |_|                   |_|   |___|                
          :) = +$   :( = -$    v%s
     https://github.com/shirosaidev/stocksight
            \033[0m""" % (color, STOCKSIGHT_VERSION)
        print(banner + '\n')

    # create instance of elasticsearch
    es = Elasticsearch(
        hosts=[{'host': elasticsearch_host, 'port': elasticsearch_port, 'scheme': 'http'}],
        verify_certs=False,
        basic_auth=(elasticsearch_user, elasticsearch_password)
        )

    # set up elasticsearch mappings and create index
    mappings = {
        "mappings": {
            "properties": {
                "type": { "type": "keyword" },
                "author": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "location": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "language": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "friends": {
                    "type": "long"
                },
                "followers": {
                    "type": "long"
                },
                "statuses": {
                    "type": "long"
                },
                "occurred": {
                    "type": "date"
                },
                "message": {
                    "type": "text",
                    "fields": {
                        "english": {
                            "type": "text",
                            "analyzer": "english"
                        },
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "tweet_id": {
                    "type": "long"
                },
                "polarity": {
                    "type": "float"
                },
                "subjectivity": {
                    "type": "float"
                },
                "sentiment": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                }
            }
        }
    }

    if args.delindex:
        logger.info('Deleting existing Elasticsearch index ' + args.index)
        es.indices.delete(index=args.index, ignore=[400, 404])

    logger.info('Creating new Elasticsearch index or using existing ' + args.index)
    es.indices.create(index=args.index, body=mappings, ignore=[400, 404])

    # check if we need to override any tokens
    if args.overridetokensreq:
        nltk_tokens_required = tuple(args.overridetokensreq)
    if args.overridetokensignore:
        nltk_tokens_ignored = tuple(args.overridetokensignore)

    # are we grabbing news headlines from yahoo finance or twitter
    if args.newsheadlines:
        try:
            url = "https://finance.yahoo.com/quote/%s/?p=%s" % (args.symbol, args.symbol)

            logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
            logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
            logger.info("Scraping news for %s from %s ..." % (args.symbol, url))

            # create instance of NewsHeadlineListener
            newslistener = NewsHeadlineListener(logger, args, es, args.symbol, url, args.frequency)
        except KeyboardInterrupt:
            print("Ctrl-c keyboard interrupt, exiting...")
            sys.exit(0)

    else:

        # set twitter keys/tokens
        # auth = OAuthHandler(consumer_key, consumer_secret)
        # auth.set_access_token(access_token, access_token_secret)
        client = Client(bearer_token)

        # create instance of the tweepy stream
        #stream = Stream(auth, tweetlistener)
        stream = TweetStreamingClient(bearer_token)

        # grab any twitter users from links in web page at url
        if args.url:
            twitter_users = get_twitter_users_from_url(args.url)
            if len(twitter_users) > 0:
                twitter_feeds = twitter_users
            else:
                logger.info("No twitter users found in links on web page, exiting")
                sys.exit(1)

        # grab twitter users from file
        if args.file:
            twitter_users = get_twitter_users_from_file(args.file)
            if len(twitter_users) > 0:
                useridlist = twitter_users
            else:
                logger.info("No twitter users found in file, exiting")
                sys.exit(1)
        elif args.keywords is None:
            # build user id list from user names
            logger.info("Looking up Twitter user ids from usernames... (use -f twitteruserids.txt for cached user ids)")
            useridlist = []
            while True:
                for u in twitter_feeds:
                    try:
                        # get user id from screen name using twitter api
                        user = client.get_user(username=u)
                        uid = str(user.data.id)
                        if uid not in useridlist:
                            useridlist.append(uid)
                        time.sleep(randrange(2, 5))
                    except TweepyException as te:
                        # sleep a bit in case twitter suspends us
                        logger.warning("Tweepy exception: twitter api error caused by: %s" % te)
                        logger.info("Sleeping for a random amount of time and retrying...")
                        time.sleep(randrange(2, 30))
                        continue
                    except KeyboardInterrupt:
                        logger.info("Ctrl-c keyboard interrupt, exiting...")
                        stream.disconnect()
                        sys.exit(0)
                break

            if len(useridlist) > 0:
                logger.info('Writing twitter user ids to text file %s' % twitter_users_file)
                try:
                    f = open(twitter_users_file, "wt", encoding='utf-8')
                    for i in useridlist:
                        line = str(i) + "\n"
                        if type(line) is bytes:
                            line = line.decode('utf-8')
                        f.write(line)
                    f.close()
                except (IOError, OSError) as e:
                    logger.warning("Exception: error writing to file caused by: %s" % e)
                    pass
                except Exception as e:
                    raise

        try:
            # search twitter for keywords
            logger.info('Stock symbol: ' + str(args.symbol))
            logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
            logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
            logger.info('Listening for Tweets (ctrl-c to exit)...')
            rules=stream.get_rules()
            if rules:
                logger.info('Removing rules: '+str(rules))
                stream.delete_rules([rule.id for rule in rules.data])
            if args.keywords is None:
                logger.info('No keywords entered, following Twitter users...')
                logger.info('Twitter Feeds: ' + str(twitter_feeds))
                logger.info('Twitter User Ids: ' + str(useridlist))
                stream.add_rules(StreamRule(value='('+' OR '.join(['from:'+ u for u in useridlist])+') lang:en -is:retweet -RT'))
                stream.filter(tweet_fields="id,text,created_at,author_id",user_fields="username,location,public_metrics",expansions="author_id")
            else:
                # keywords to search on twitter
                # add keywords to list
                keywords = args.keywords.split(',')
                if args.addtokens:
                    # add tokens to keywords to list
                    for f in nltk_tokens_required:
                        keywords.append(f)
                logger.info('Searching Twitter for keywords...')
                logger.info('Twitter keywords: ' + str(keywords))
                stream.add_rules(StreamRule(value='"'+'" "'.join(keywords)+'" lang:en -is:retweet -RT'))
                stream.filter(tweet_fields="id,text,created_at,author_id",user_fields="username,location,public_metrics",expansions="author_id")
        except TweepyException as te:
            logger.debug("Tweepy Exception: Failed to get tweets caused by: %s" % te)
        except KeyboardInterrupt:
            print("Ctrl-c keyboard interrupt, exiting...")
            stream.disconnect()
            sys.exit(0)
