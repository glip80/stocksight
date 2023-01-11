import pandas as pd

from finviz_scrapper import NewsScrapper
# from sentiment import nltk_tokens_ignored
from sentiment_analysis import SentimentAnalysis


class NewsHeadlineListener:

    def __init__(self, logger, args, es, symbol: str, url=None, frequency=120):
        self.url = url
        self.logger = logger
        self.headlines = []
        self.followedlinks = []
        self.frequency = frequency
        self.count = 0
        self.count_filtered = 0
        self.filter_ratio = 0
        self.sa = SentimentAnalysis(logger, args)
        self.news = NewsScrapper(None, None)

        news = pd.read_csv('NVDA.csv')
        analysed = self.sa.analyse(news)

        for index, row in analysed.iterrows():
            logger.info("Adding news headline to elasticsearch")
            # add news headline data and sentiment info to elasticsearch
            es.index(index=args.index,
                     doc_type="_doc",
                     body={
                         "type": "newsheadline",
                         "occurred": pd.to_datetime(row['datetime']).isoformat(),
                         "location": row['link'],
                         "message": row['title'],
                         "polarity": row['polarity'],
                         "subjectivity": row['subjectivity'],
                         "sentiment": row['sentiment']
                     })
            # for index, row in df.iterrows():
            #     # add any new headlines
            #     # for htext, htext_url in new_headlines:
            #     title = row['title']
            #     if title not in self.headlines:
            #         self.headlines.append(title)
            #         self.count += 1
            #
            #         datenow = datetime.utcnow().isoformat()
            #         # output news data
            #         print("\n------------------------------> (news headlines: %s, filtered: %s, filter-ratio: %s)" \
            #               % (
            #               self.count, self.count_filtered, str(round(self.count_filtered / self.count * 100, 2)) + "%"))
            #         print("Date: " + datenow)
            #         print("News Headline: " + str(title))
            #         print("Location (url): " + str(row['link']))
            #
            #         # create tokens of words in text using nltk
            #         text_for_tokens = re.sub(
            #             r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", str(title))
            #         tokens = nltk.word_tokenize(text_for_tokens)
            #         print("NLTK Tokens: " + str(tokens))
            #
            #         # check for min token length
            #         if len(tokens) < 5:
            #             logger.info("Text does not contain min. number of tokens, not adding")
            #             self.count_filtered += 1
            #             continue
            #
            #         # check ignored tokens from config
            #         for t in nltk_tokens_ignored:
            #             if t in tokens:
            #                 logger.info("Text contains token from ignore list, not adding")
            #                 self.count_filtered += 1
            #                 continue
            #         # check required tokens from config
            #         # tokenspass = False
            #         # for t in nltk_tokens_required:
            #         #     if t in tokens:
            #         #         tokenspass = True
            #         #         break
            #         # if not tokenspass:
            #         #     logger.info("Text does not contain token from required list, not adding")
            #         #     self.count_filtered+=1
            #         #     continue
            #
            #         # get sentiment values
            #         polarity, subjectivity, sentiment = sentiment_analysis(title)
            #
            #         logger.info("Adding news headline to elasticsearch")
            #         # add news headline data and sentiment info to elasticsearch
            #         es.index(index=args.index,
            #                  doc_type="_doc",
            #                  body={"date": datenow,
            #                        "type": "newsheadline",
            #                        "location": row['link'],
            #                        "message": title,
            #                        "polarity": polarity,
            #                        "subjectivity": subjectivity,
            #                        "sentiment": sentiment})
            #
            logger.info("Will get news headlines again in %s sec..." % self.frequency)
            # time.sleep(self.frequency)

    # def get_news_headlines(self, url):
    #
    #     latestheadlines = []
    #     latestheadlines_links = []
    #     parsed_uri = urlparse.urljoin(url, '/')
    #
    #     try:
    #
    #         req = requests.get(url)
    #         html = req.text
    #         soup = BeautifulSoup(html, 'html.parser')
    #         html = soup.findAll('h3')
    #         links = soup.findAll('a')
    #
    #         logger.debug(html)
    #         logger.debug(links)
    #
    #         if html:
    #             for i in html:
    #                 latestheadlines.append((i.next.next.next.next, url))
    #         logger.debug(latestheadlines)
    #
    #         if args.followlinks:
    #             if links:
    #                 for i in links:
    #                     if '/news/' in i['href']:
    #                         l = parsed_uri.rstrip('/') + i['href']
    #                         if l not in self.followedlinks:
    #                             latestheadlines_links.append(l)
    #                             self.followedlinks.append(l)
    #             logger.debug(latestheadlines_links)
    #
    #             logger.info("Following any new links and grabbing text from page...")
    #
    #             for linkurl in latestheadlines_links:
    #                 for p in get_page_text(linkurl):
    #                     latestheadlines.append((p, linkurl))
    #             logger.debug(latestheadlines)
    #
    #     except requests.exceptions.RequestException as re:
    #         logger.warning("Exception: can't crawl web site (%s)" % re)
    #         pass
    #
    #     return latestheadlines

# def get_page_text(url):
#     max_paragraphs = 10
#
#     try:
#         logger.debug(url)
#         req = requests.get(url)
#         html = req.text
#         soup = BeautifulSoup(html, 'html.parser')
#         html_p = soup.findAll('p')
#
#         logger.debug(html_p)
#
#         if html_p:
#             n = 1
#             for i in html_p:
#                 if n <= max_paragraphs:
#                     if i.string is not None:
#                         logger.debug(i.string)
#                         yield i.string
#                 n += 1
#
#     except requests.exceptions.RequestException as re:
#         logger.warning("Exception: can't crawl web site (%s)" % re)
#         pass
