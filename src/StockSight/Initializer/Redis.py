#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis Global handler


Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import redis
import os
from StockSight.Initializer.ConfigReader import config

rds = redis.Redis(
    host=str(os.getenv('REDIS_HOST', config['redis']['host'])),
    port=os.getenv('REDIS_PORT', config['redis']['port']),
    db=os.getenv('REDIS_DB', config['redis']['db']),
    password=os.getenv('REDIS_PASSWORD', config['redis']['password'])
)
