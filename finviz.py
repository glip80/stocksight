# https://github.com/BabakBar/Stock-Sentiment-Analysis-Finviz/blob/main/Stock%20Sentiment.ipynb
# https://github.com/damianboh/stock_news_sentiment_analysis/blob/master/Sentiment%20Analysis%20of%20Financial%20News%20Headlines.ipynb
# source https://github.com/mkstar-2000/NFAGated/blob/master/pages/03_Sentiment_Analysis_From_FinViz.py
# run py -m streamlit run finviz.py

# Dashboard
import streamlit as st
# get data
from urllib.request import urlopen, Request
# parse data from FinViz
from bs4 import BeautifulSoup
import os

# manipulate and store the data in DataFrames
import pandas as pd

# plot the sentiment on a chart
import matplotlib.pyplot as plt

# NLTK VADER for sentiment analysis on the news headlines
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# nltk.download('vader_lexicon')

# wordcloud and stop words
from wordcloud import WordCloud, STOPWORDS

# take the raw part of the url, we will append the ticker to the end of the link to pull up its data
# Extract data from finviz use the raw url.
finwiz_url = 'https://finviz.com/quote.ashx?t='

tickers = (
    'AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CSCO', 'CVX', 'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'KO', 'JPM', 'MCD',
    'MMM',
    'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'CRM', 'VZ', 'V', 'WBA', 'WMT', 'DIS', 'DOW')
tickers_dropdown = st.selectbox('Choose a stock ticker', tickers)

# Initiate an empty dictionary to hold the news tables from website
news_tables = {}
tickers = [tickers_dropdown]

for ticker in tickers:
    url = finwiz_url + ticker
    req = Request(url=url,
                  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'})
    response = urlopen(req)
    # Read the contents of the file into 'html'
    html = BeautifulSoup(response, "lxml")
    # Find 'news-table' in the Soup and load it into 'news_table'
    news_table = html.find(id='news-table')
    # Add the table to our dictionary
    news_tables[ticker] = news_table

# <td> tag defines the standard cells in the table which are displayed as normal-weight, left-aligned text.
# <tr> tag defines the table rows.

# Read headlines for 'stock'
stock = news_tables[tickers_dropdown]
# Get all the table rows tagged in HTML with <tr> into 'stock_tr'
stock_tr = stock.findAll('tr')

# Create a list to append the titles
title_list = []
ingore_list = ['stock', 'stocks', 'prediction']


def find_words(text_array, search):
    """Find exact words"""
    lower = search.lower()
    for text in text_array:
        if text in lower:
            return True
    return False


# The enumerate() function takes a collection and returns it as an enumerate object.
for index, table_row in enumerate(stock_tr):
    # Read the text of the element 'a' (Anchor tag) into 'title'
    title = table_row.a.text
    if not find_words(ingore_list, title):
        # Read the text of the element 'td' into 'timestamp' for the timestamp
        timestamp = table_row.td.text.split()

        # if the length of 'timestamp' is 1, load 'time' as the only element
        if len(timestamp) == 1:
            time = timestamp[0]

        # else load 'date' as the 1st element and 'time' as the second
        else:
            date = timestamp[0]
            time = timestamp[1]
        ticker = tickers

        # Append the title and timestamp to list format.
        title_list.append([tickers, date, time, title])
        # Create a dataframe using the 'title_list'
        finviz_headlines = pd.DataFrame(title_list, columns=[['ticker', 'date', 'time', 'title']])

st.subheader("Most recent 100 Headlines")
st.write(finviz_headlines)


# Sentiment calculation based on compound score
def get_sentiment(score):
    """
    Calculates the sentiment based on the compound score.
    """
    result = 0  # Neutral by default
    if score >= 0.05:  # Positive
        result = 1
    elif score <= -0.05:  # Negative
        result = -1

    return result


# Instantiate the sentiment intensity analyzer with the existing lexicon
# Create the sentiment scores DataFrame
analyzer = SentimentIntensityAnalyzer()

# New words and values
new_words = {
    'update': 30,
    'crushes': 10,
    'beats': 5,
    'misses': -5,
    'trouble': -10,
    'falls': -100,
}
# Update the lexicon
analyzer.lexicon.update(new_words)

title_sent = {
    "title_compound": [],
    "title_pos": [],
    "title_neu": [],
    "title_neg": [],
    "title_sent": [],
}

# Get sentiment for the title
for index, row in finviz_headlines.iterrows():
    try:
        # Sentiment scoring with VADER
        title_sentiment = analyzer.polarity_scores(row["title"])
        sentiment = get_sentiment(title_sentiment["compound"])
        title_sent["title_compound"].append(title_sentiment["compound"])
        title_sent["title_pos"].append(title_sentiment["pos"])
        title_sent["title_neu"].append(title_sentiment["neu"])
        title_sent["title_neg"].append(title_sentiment["neg"])
        title_sent["title_sent"].append(sentiment)
    except AttributeError:
        pass

# Attaching sentiment columns to the News DataFrame
title_sentiment_df = pd.DataFrame(title_sent)
finviz_headlines = finviz_headlines.join(title_sentiment_df)

st.subheader("Sentiment Detailed after filter")
#filter non relevant news
non_neutral = finviz_headlines.loc[finviz_headlines['title_sent'] != 0]
st.write(non_neutral)

st.subheader("Sentiment Statistics")
st.write(non_neutral.describe())


###
# ADD PIE CHART FROM TWITTER!!
###

def word_cloud(text):
    stopwords = set(STOPWORDS)
    allWords = ' '.join([title for title in text])
    wordCloud = WordCloud(background_color='black', width=1600, height=800, stopwords=stopwords, min_font_size=20,
                          max_font_size=150, colormap='prism').generate(allWords)
    fig, ax = plt.subplots(figsize=(20, 10), facecolor='k')
    plt.imshow(wordCloud)
    ax.axis("off")
    fig.tight_layout(pad=0)
    plt.show()
    st.pyplot(plt)


st.subheader("Wordcloud for further analysis")
word_cloud(non_neutral[('title',)].values)
