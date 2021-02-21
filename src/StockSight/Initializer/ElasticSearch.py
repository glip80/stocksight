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
from requests_aws4auth import AWS4Auth
import os
from settings import PRODUCTION_MODE

from StockSight.Initializer.ConfigReader import config


if PRODUCTION_MODE:
    region = os.getenv('AWS_REGION')
    service = 'es'
    credentials = boto3.Session().get_credentials()
    http_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    verify_certs = True
else:
    http_auth =(
        os.getenv('ELASTICSEARCH_USER', config['elasticsearch']['user']),
        os.getenv('ELASTICSEARCH_PASSWORD', config['elasticsearch']['password']),
    )
    verify_certs = False


# create instance of elasticsearch
es = Elasticsearch(
    hosts=[{
        'host': os.getenv('ELASTICSEARCH_HOST', config['elasticsearch']['host']),
        'port': os.getenv('ELASTICSEARCH_PORT', config['elasticsearch']['port'])
        }],
    http_auth= http_auth,
    scheme=os.getenv('ELASTICSEARCH_SCHEME', config['elasticsearch']['scheme']),
    use_ssl = True,
    verify_certs = verify_certs,
    connection_class=RequestsHttpConnection
    )
