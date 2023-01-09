#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Global Elastic Search Handler

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from kibana import Kibana
import os

from StockSight.Initializer.ConfigReader import config
from settings import PRODUCTION_MODE

from StockSight.Initializer.ConfigReader import config


if PRODUCTION_MODE:
    from requests_aws4auth import AWS4Auth
    import boto3

    region = os.getenv('AWS_REGION')
    service = 'es'
    credentials = boto3.Session().get_credentials()
    http_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    verify_certs = True
else:
    http_auth =(
        config.kibana['user'],
        config.kibana['password']
        )
    verify_certs = False


# create instance of kibana
kibana = Kibana.Client(
    host=config.kibana['host'],
    port=config.kibana['port'],
    http_auth=http_auth,
    scheme=config.kibana['scheme'],
    mount_path=config.kibana['mount_path'],
    verify_certs=verify_certs,
)
