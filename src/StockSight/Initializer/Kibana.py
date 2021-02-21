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

# create instance of kibana
kibana = Kibana.Client(
    host=os.getenv('KIBANA_HOST', config['kibana']['host']),
    port=os.getenv('KIBANA_PORT', config['kibana']['port']),
    http_auth=(
        os.getenv('KIBANA_USER', config['kibana']['user']),
        os.getenv('KIBANA_PASSWORD', config['kibana']['password'])
        ),
    scheme=os.getenv('KIBANA_SCHEME', config['kibana']['scheme']),
    mount_path=os.getenv('KIBANA_MOUNT_PATH', config['kibana']['mount_path']),
    verify_certs=False,
)
