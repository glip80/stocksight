import os

elasticsearch = {
    "host": os.getenv('ELASTICSEARCH_HOST', "elasticsearch"), 
    "table_prefix": {
      "price": "stocksight_price_", 
      "sentiment": "stocksight_sentiment_"
    }, 
    "user": os.getenv('ELASTICSEARCH_USER', "admin"), 
    "scheme": os.getenv('ELASTICSEARCH_SCHEME', "https"), 
    "password": os.getenv('ELASTICSEARCH_PASSWORD', "admin"), 
    "port": int(os.getenv('ELASTICSEARCH_PORT', 9200))
  }

spawn_intervals = {
    "request_min": 1, 
    "news_min": 5, 
    "stockprice_max": 0, 
    "stockprice_min": 0, 
    "news_max": 10, 
    "request_max": 3
  }

sentiment_analyzer = {
    "ignore_words": [
      "win", 
      "giveaway", 
      "vs", 
      "vs."
    ]
  }

twitter = {
    "consumer_secret": os.getenv('TWITTER_CONSUMER_SECRET'), 
    "consumer_key": os.getenv('TWITTER_CONSUMER_KEY'), 
    "access_token": os.getenv('TWITTER_ACCESS_TOKEN'), 
    "access_token_secret": os.getenv('TWITTER_ACCESS_TOKEN_SECRET'), 
    "feeds": [
      "@elonmusk", 
      "@stockwits", 
      "@nytimes", 
      "@MorganStanley", 
      "@GoldmanSachs", 
      "@WSJmarkets", 
      "@WashingtonPost", 
      "@nytimesbusiness", 
      "@reutersbiz"
    ], 
    "min_followers": 1000
  }

redis = {
    "host": os.getenv('REDIS_HOST', "redis"), 
    "password": os.getenv('REDIS_PASSWORD', None), 
    "db": os.getenv('REDIS_DB', 0), 
    "port": os.getenv('REDIS_PORT', 6379)
  }

kibana=  {
    "host": os.getenv('KIBANA_HOST', "kibana"), 
    "scheme": os.getenv('KIBANA_SCHEME', "http"), 
    "mount_path": os.getenv('KIBANA_MOUNT_PATH', None), 
    "port": int(os.getenv('KIBANA_PORT', 5601)), 
    "user": os.getenv('KIBANA_USER', "admin"),
    "password": os.getenv('KIBANA_PASSWORD', "admin")
  }

stock_price = {
    "hour_end": 17, 
    "weekday_end": 4, 
    "hour_start": 9, 
    "time_check": False, 
    "timezone_str": "America/New_York", 
    "weekday_start": 0
  }

symbols = {
    "amd": [
      "amd", 
      "ryzen", 
      "epyc", 
      "radeon", 
      "crossfire", 
      "threadripper"
    ], 
    "tsla": [
      "tesla", 
      "tsla", 
      "elonmusk", 
      "elon", 
      "musk"
    ]
  }

news= {
    "follow_link": True
  }

console_output_mode= "normal"