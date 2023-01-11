import json
import re
import string
import time
from random import randrange
from urllib import parse as urlparse

import nltk
import requests
from bs4 import BeautifulSoup
from newspaper import Article, ArticleException
from tweepy import StreamingClient

from config import nltk_min_tokens
from sentiment import logger, args, clean_text, nltk_tokens_ignored, nltk_tokens_required, \
    es
from sentiment_analysis import clean_text_sentiment, sentiment_analysis

# tweet id list
tweet_ids = []


class TweetStreamingClient(StreamingClient):

    def __init__(self, bearer_token):
        super().__init__(bearer_token)
        self.count = 0
        self.count_filtered = 0
        self.filter_ratio = 0

    # on success
    def on_data(self, data):
        try:

            if self.count > 0:
                print("\n------------------------------> (tweets: %s, filtered: %s, filter-ratio: %s)" \
                      % (self.count, self.count_filtered, str(round(self.count_filtered / self.count * 100, 2)) + "%"))

            self.count += 1
            # decode
            dict_data = json.loads(data)

            logger.debug('tweet data: ' + str(dict_data))

            text = dict_data["data"]["text"]
            if text is None:
                logger.info("Tweet has no relevant text, skipping")
                self.count_filtered += 1
                return True

            # grab html links from tweet
            tweet_urls = []
            if args.linksentiment:
                tweet_urls = re.findall(r'(https?://[^\s]+)', text)

            # clean up tweet text
            textclean = clean_text(text)

            # check if tweet has no valid text
            if textclean == "":
                logger.info("Tweet does not cotain any valid text after cleaning, not adding")
                self.count_filtered += 1
                return True

            # get date when tweet was created
            # created_date = time.strftime(
            #     '%Y-%m-%dT%H:%M:%S', time.strptime(dict_data['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))
            created_date = dict_data["data"]['created_at']

            # store dict_data into vars
            screen_name = str(dict_data["includes"]["users"][0]["username"])
            location = str(dict_data["includes"]["users"][0].get("location"))
            language = "en"
            friends = int(dict_data["includes"]["users"][0]["public_metrics"]["following_count"])
            followers = int(dict_data["includes"]["users"][0]["public_metrics"]["followers_count"])
            statuses = int(dict_data["includes"]["users"][0]["public_metrics"]["tweet_count"])
            text_filtered = str(textclean)
            tweetid = int(dict_data["data"]["id"])
            text_raw = str(dict_data["data"]["text"])

            # output twitter data
            print("\n<------------------------------")
            print("Tweet Date: " + created_date)
            print("Screen Name: " + screen_name)
            print("Location: " + location)
            print("Language: " + language)
            print("Friends: " + str(friends))
            print("Followers: " + str(followers))
            print("Statuses: " + str(statuses))
            print("Tweet ID: " + str(tweetid))
            print("Tweet Raw Text: " + text_raw)
            print("Tweet Filtered Text: " + text_filtered)

            # create tokens of words in text using nltk
            text_for_tokens = re.sub(
                r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", text_filtered)
            tokens = nltk.word_tokenize(text_for_tokens)
            # convert to lower case
            tokens = [w.lower() for w in tokens]
            # remove punctuation from each word
            table = str.maketrans('', '', string.punctuation)
            stripped = [w.translate(table) for w in tokens]
            # remove remaining tokens that are not alphabetic
            tokens = [w for w in stripped if w.isalpha()]
            # filter out stop words
            stop_words = set(nltk.corpus.stopwords.words('english'))
            tokens = [w for w in tokens if not w in stop_words]
            # remove words less than 3 characters
            tokens = [w for w in tokens if not len(w) < 3]
            print("NLTK Tokens: " + str(tokens))

            # check for min token length
            if len(tokens) < 5:
                logger.info("Tweet does not contain min. number of tokens, not adding")
                self.count_filtered += 1
                return True

            # do some checks before adding to elasticsearch and crawling urls in tweet
            if friends == 0 or \
                    followers == 0 or \
                    statuses == 0 or \
                    text == "" or \
                    tweetid in tweet_ids:
                logger.info("Tweet doesn't meet min requirements, not adding")
                self.count_filtered += 1
                return True

            # check ignored tokens from config
            for t in nltk_tokens_ignored:
                if t in tokens:
                    logger.info("Tweet contains token from ignore list, not adding")
                    self.count_filtered += 1
                    return True
            # check required tokens from config
            tokenspass = False
            tokensfound = 0
            for t in nltk_tokens_required:
                if t in tokens:
                    tokensfound += 1
                    if tokensfound == nltk_min_tokens:
                        tokenspass = True
                        break
            if not tokenspass:
                logger.info("Tweet does not contain token from required list or min required, not adding")
                self.count_filtered += 1
                return True

            # clean text for sentiment analysis
            text_clean = clean_text_sentiment(text_filtered)

            # check if tweet has no valid text
            if text_clean == "":
                logger.info("Tweet does not cotain any valid text after cleaning, not adding")
                self.count_filtered += 1
                return True

            print("Tweet Clean Text (sentiment): " + text_clean)

            # get sentiment values
            polarity, subjectivity, sentiment = sentiment_analysis(text_clean)

            # add tweet_id to list
            tweet_ids.append(dict_data["data"]["id"])

            # get sentiment for tweet
            if len(tweet_urls) > 0:
                tweet_urls_polarity = 0
                tweet_urls_subjectivity = 0
                for url in tweet_urls:
                    res = tweeklink_sentiment_analysis(url)
                    if res is None:
                        continue
                    pol, sub, sen = res
                    tweet_urls_polarity = (tweet_urls_polarity + pol) / 2
                    tweet_urls_subjectivity = (tweet_urls_subjectivity + sub) / 2
                    if sentiment == "positive" or sen == "positive":
                        sentiment = "positive"
                    elif sentiment == "negative" or sen == "negative":
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"

                # calculate average polarity and subjectivity from tweet and tweet links
                if tweet_urls_polarity > 0:
                    polarity = (polarity + tweet_urls_polarity) / 2
                if tweet_urls_subjectivity > 0:
                    subjectivity = (subjectivity + tweet_urls_subjectivity) / 2

            logger.info("Adding tweet to elasticsearch")
            # add twitter data and sentiment info to elasticsearch
            es.index(index=args.index,
                     body={"author": screen_name,
                           "type": "tweet",
                           "location": location,
                           "language": language,
                           "friends": friends,
                           "followers": followers,
                           "statuses": statuses,
                           "date": created_date,
                           "message": text_filtered,
                           "tweet_id": tweetid,
                           "polarity": polarity,
                           "subjectivity": subjectivity,
                           "sentiment": sentiment})

            # randomly sleep to stagger request time
            time.sleep(randrange(2, 5))
            return True

        except Exception as e:
            logger.warning("Exception: exception caused by: %s" % e)
            raise

    # on failure
    def on_error(self, status_code):
        logger.error("Got an error with status code: %s (will try again later)" % status_code)
        # randomly sleep to stagger request time
        time.sleep(randrange(2, 30))
        return True

    # on timeout
    def on_timeout(self):
        logger.warning("Timeout... (will try again later)")
        # randomly sleep to stagger request time
        time.sleep(randrange(2, 30))
        return True


def tweeklink_sentiment_analysis(url):
    # get text summary of tweek link web page and run sentiment analysis on it
    try:
        logger.info('Following tweet link %s to get sentiment..' % url)
        article = Article(url)
        article.download()
        article.parse()
        # check if twitter web page
        if "Tweet with a location" in article.text:
            logger.info('Link to Twitter web page, skipping')
            return None
        article.nlp()
        tokens = article.keywords
        print("Tweet link nltk tokens:", tokens)

        # check for min token length
        if len(tokens) < 5:
            logger.info("Tweet link does not contain min. number of tokens, not adding")
            return None
        # check ignored tokens from config
        for t in nltk_tokens_ignored:
            if t in tokens:
                logger.info("Tweet link contains token from ignore list, not adding")
                return None
        # check required tokens from config
        tokenspass = False
        tokensfound = 0
        for t in nltk_tokens_required:
            if t in tokens:
                tokensfound += 1
                if tokensfound == nltk_min_tokens:
                    tokenspass = True
                    break
        if not tokenspass:
            logger.info("Tweet link does not contain token from required list or min required, not adding")
            return None

        summary = article.summary
        if summary == '':
            logger.info('No text found in tweet link url web page')
            return None
        summary_clean = clean_text(summary)
        summary_clean = clean_text_sentiment(summary_clean)
        print("Tweet link Clean Summary (sentiment): " + summary_clean)
        polarity, subjectivity, sentiment = sentiment_analysis(summary_clean)

        return polarity, subjectivity, sentiment

    except ArticleException as e:
        logger.warning('Exception: error getting text on Twitter link caused by: %s' % e)
        return None

def clean_text_sentiment(text):
    # clean up text for sentiment analysis
    text = re.sub(r"[#|@]\S+", "", text)
    text = text.strip()
    return text

def get_twitter_users_from_url(url):
    twitter_users = []
    logger.info("Grabbing any twitter users from url %s" % url)
    try:
        twitter_urls = ("http://twitter.com/", "http://www.twitter.com/",
                        "https://twitter.com/", "https://www.twitter.com/")
        # req_header = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38"}
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        html_links = []
        for link in soup.findAll('a'):
            html_links.append(link.get('href'))
        if html_links:
            for link in html_links:
                # check if twitter_url in link
                parsed_uri = urlparse.urljoin(link, '/')
                # get twitter user name from link and add to list
                if parsed_uri in twitter_urls and "=" not in link and "?" not in link:
                    user = link.split('/')[3]
                    twitter_users.append(u'@' + user)
            logger.debug(twitter_users)
    except requests.exceptions.RequestException as re:
        logger.warning("Requests exception: can't crawl web site caused by: %s" % re)
        pass
    return twitter_users


def get_twitter_users_from_file(file):
    # get twitter user ids from text file
    twitter_users = []
    logger.info("Grabbing any twitter user ids from file %s" % file)
    try:
        f = open(file, "rt", encoding='utf-8')
        for line in f.readlines():
            u = line.strip()
            twitter_users.append(u)
        logger.debug(twitter_users)
        f.close()
    except (IOError, OSError) as e:
        logger.warning("Exception: error opening file caused by: %s" % e)
        pass
    return twitter_users
