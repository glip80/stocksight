import logging
import pandas as pd
import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# sentiment text-processing url
sentimentURL = 'http://text-processing.com/api/sentiment/'


class SentimentAnalysis:

    def __init__(self, logger, args):
        self.args = args
        self.logger = logger
        self.analyzer = SentimentIntensityAnalyzer()
        # New words and values
        new_words = {
            'update': 30,
            'crushes': 10,
            'beats': 5,
            'misses': -5,
            'trouble': -10,
            'falls': -100,
        }
        self.ingore_list = ['stock', 'stocks', 'prediction']

        # Update the lexicon
        self.analyzer.lexicon.update(new_words)

    def find_words(self, text_array, search):
        """Find exact words"""
        lower = search.lower()
        for text in text_array:
            if text in lower:
                return True
        return False

    # Sentiment calculation based on compound score
    def get_sentiment(self, text, score):
        """
        Calculates the sentiment based on the compound score.
        """
        # pass text into TextBlob
        text_tb = TextBlob(text)
        sentiment_ = 0
        if text_tb.sentiment.polarity < 0 and score <= -0.05:
            sentiment_ = -1
        elif text_tb.sentiment.polarity > 0 and score >= 0.05:
            sentiment_ = 1
        # calculate average polarity from TextBlob and VADER
        polarity = (text_tb.sentiment.polarity + score) / 2
        return sentiment_, round(polarity, 3), round(text_tb.sentiment.subjectivity, 3)

    def analyse(self, headlines):
        title_sent = {
            "ignored": [],
            "compound": [],
            "positive": [],
            "neutral": [],
            "negative": [],
            "sentiment": [],
            "polarity": [],
            "subjectivity": [],
        }

        # Get sentiment for the title
        for index, row in headlines.iterrows():
            try:
                # Sentiment scoring with VADER
                title = row["title"]
                title_sentiment = self.analyzer.polarity_scores(title)
                sentiment, polarity, subjectivity, = self.get_sentiment(title, title_sentiment["compound"])
                title_sent["ignored"].append(self.find_words(self.ingore_list, title))
                title_sent["compound"].append(title_sentiment["compound"])
                title_sent["positive"].append(title_sentiment["pos"])
                title_sent["neutral"].append(title_sentiment["neu"])
                title_sent["negative"].append(title_sentiment["neg"])
                title_sent["sentiment"].append(sentiment)
                title_sent["polarity"].append(polarity)
                title_sent["subjectivity"].append(subjectivity)
            except AttributeError:
                pass

        # Attaching sentiment columns to the News DataFrame
        title_sentiment_df = pd.DataFrame(title_sent)
        df = headlines.join(title_sentiment_df)
        # filter non relevant news
        non_neutral = df.loc[(df['ignored']==False) & (df["compound"] > 0)]
        #drop ignored field
        non_neutral.drop('ignored', axis=1, inplace=True)
        return non_neutral

    def get_sentiment_from_url(self, text, sentiment_url=None):
        # get sentiment from text processing website
        payload = {'text': text}

        try:
            # logger.debug(text)
            post = requests.post(sentiment_url, data=payload)
            # logger.debug(post.status_code)
            # logger.debug(post.text)
        except requests.exceptions.RequestException as re:
            self.logger.error("Exception: requests exception getting sentiment from url caused by %s" % re)
            raise

        # return None if we are getting throttled or other connection problem
        if post.status_code != 200:
            self.logger.warning("Can't get sentiment from url caused by %s %s" % (post.status_code, post.text))
            return None

        response = post.json()

        neg = response['probability']['neg']
        pos = response['probability']['pos']
        neu = response['probability']['neutral']
        label = response['label']

        # determine if sentiment is positive, negative, or neutral
        if label == "neg":
            sentiment = "negative"
        elif label == "neutral":
            sentiment = "neutral"
        else:
            sentiment = "positive"

        return sentiment, neg, pos, neu

    def sentiment_analysis(self, text):
        """Determine if sentiment is positive, negative, or neutral
        algorithm to figure out if sentiment is positive, negative or neutral
        uses sentiment polarity from TextBlob, VADER Sentiment and
        sentiment from text-processing URL
        could be made better :)
        """

        # pass text into sentiment url
        # if self.args.websentiment:
        #     ret = self.get_sentiment_from_url(text, sentimentURL)
        #     if ret is None:
        #         sentiment_url = None
        #     else:
        #         sentiment_url, neg_url, pos_url, neu_url = ret
        # else:
        sentiment_url = None

        # pass text into TextBlob
        text_tb = TextBlob(text)

        # pass text into VADER Sentiment
        text_vs = self.analyzer.polarity_scores(text)

        # determine sentiment from our sources
        sentiment_url = None
        if sentiment_url is None:
            if text_tb.sentiment.polarity < 0 and text_vs['compound'] <= -0.05:
                sentiment = "negative"
            elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.05:
                sentiment = "positive"
            else:
                sentiment = "neutral"
        else:
            if text_tb.sentiment.polarity < 0 and text_vs['compound'] <= -0.05 and sentiment_url == "negative":
                sentiment = "negative"
            elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.05 and sentiment_url == "positive":
                sentiment = "positive"
            else:
                sentiment = "neutral"

        # calculate average polarity from TextBlob and VADER
        polarity = (text_tb.sentiment.polarity + text_vs['compound']) / 2

        # output sentiment polarity
        print("************")
        print("Sentiment Polarity: " + str(round(polarity, 3)))

        # output sentiment subjectivity (TextBlob)
        print("Sentiment Subjectivity: " + str(round(text_tb.sentiment.subjectivity, 3)))

        # output sentiment
        print("Sentiment (url): " + str(sentiment_url))
        print("Sentiment (algorithm): " + str(sentiment))
        print("Overall sentiment (textblob): ", text_tb.sentiment)
        print("Overall sentiment (vader): ", text_vs)
        print("sentence was rated as ", round(text_vs['neg'] * 100, 3), "% Negative")
        print("sentence was rated as ", round(text_vs['neu'] * 100, 3), "% Neutral")
        print("sentence was rated as ", round(text_vs['pos'] * 100, 3), "% Positive")
        print("************")

        return polarity, text_tb.sentiment.subjectivity, sentiment


# csv = pd.read_csv('finviz.news')
# logger = logging.getLogger('stocksight')
# sa = SentimentAnalysis(logger, None)
# df = sa.analyse(csv)
# for index, row in csv.iterrows():
#     sa.sentiment_analysis(row['title'])
