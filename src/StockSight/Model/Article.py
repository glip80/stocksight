#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Article Data Holder

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import hashlib
from datetime import datetime

class Article:

    def __init__(self, title, url, body='', referer_url='', author=None, author_url=None):
        self.title = title
        self.body = body
        self.url = url
        self.referer_url = referer_url
        self.msg_id = hashlib.md5((self.title + self.url).encode()).hexdigest()
        self.published_at = datetime.utcnow()
        self.author=author
        self.author_url=author_url

    def __eq__(self, other):
        return self.msg_id and other.msg_id
