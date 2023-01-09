#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockprice.py - get stock price from Yahoo and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""


import sys, time
import threading

# from StockSight.YahooFinanceListener import *
# from StockSight.SeekAlphaListener import *
from StockSight.EsMap.Sentiment import *
from base import Symbol
from random import randint

from StockSight.StockTwitListener import *



STOCKSIGHT_VERSION = '0.2'
__version__ = STOCKSIGHT_VERSION


if __name__ == '__main__':

    try:
        
        for symbol in Symbol.objects.values_list('name', flat=True):
            try:
                logger.info('Creating new Sentiment index or using existing ' + symbol)
                es.indices.create(index=config.elasticsearch['table_prefix']['sentiment']+symbol.lower(), body=mapping, ignore=[400, 404])

                logger.info('NLTK tokens ignored: ' + str(config.sentiment_analyzer['ignore_words']))

                stocktwits_listener = StockTwitListener(symbol)
                stocktwits_thread = threading.Thread(target=stocktwits_listener.get_chatter)
                stocktwits_thread.start()

                if(config.spawn_intervals['news_min'] > 0):
                    time.sleep(randint(config.spawn_intervals['news_min'], config.spawn_intervals['news_max']))
            except Exception as e:
                logger.warning("%s" % e)
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)
