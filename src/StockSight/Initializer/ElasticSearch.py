#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Global Elastic Search Handler

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from elasticsearch import Elasticsearch, RequestsHttpConnection
import os

from StockSight.Initializer.ConfigReader import config

# create instance of elasticsearch
es = Elasticsearch(
    hosts=[{
        'host': os.getenv('ELASTICSEARCH_HOST', config['elasticsearch']['host']),
        'port': os.getenv('ELASTICSEARCH_PORT', config['elasticsearch']['port'])
        }],
    http_auth=(
        os.getenv('ELASTICSEARCH_USER', config['elasticsearch']['user']),
        os.getenv('ELASTICSEARCH_PASSWORD', config['elasticsearch']['password']),
        ),
    scheme=os.getenv('ELASTICSEARCH_SCHEME', config['elasticsearch']['scheme']),
    verify_certs=False,
    # connection_class=RequestsHttpConnection
    )
