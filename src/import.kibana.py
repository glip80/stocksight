#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import.kibana.py - import kabana visual for each defined symbol
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
# import requests
import sys
import os
import tempfile
from StockSight.Initializer.ConfigReader import *
from base import Symbol, SymbolAlias, TwitterUser
from StockSight.Initializer.Kibana import kibana


STOCKSIGHT_VERSION = '0.2'
__version__ = STOCKSIGHT_VERSION

if __name__ == '__main__':

    try:
        template_file = open('kibana_export/export.7.3.ndjson', "rt", encoding='utf-8')
        import_template = template_file.read()
        template_file.close()

        for symbol in Symbol.objects.values_list('name', flat=True):
            try:
                print("Starting %s Kibana Dashboard Import" % symbol)
                with tempfile.NamedTemporaryFile(suffix='.ndjson') as ndjson_file:
                    final_text = import_template.replace('tmpl', symbol)
                    ndjson_file.write(bytes(final_text, encoding = 'utf-8'))
                    ndjson_file.seek(0)

                    overwrite = os.getenv('KIBANA_OVERWRITE', False)
                    if overwrite is False:
                        payload = {}
                    else:
                        payload = {'overwrite': 'true'}
                    
                    post = kibana.import_saved_objects(ndjson_file, payload)

                print("Imported %s Kibana Dashboard" % symbol)
                print(post.text)

            except Exception as e:
                print(e)
                print("Please run this script manually once kibana is ready.")
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)
