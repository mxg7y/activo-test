#! python3
# test.py

from fetch_corpus_data import GoogleScrap, CrawlingText, FormatCorpusData
import pprint

google = GoogleScrap('ふるさとチョイス', numpages=8)
google.search_with_google()

fcd = FormatCorpusData('ふるさとチョイス')

with open('corpus.txt', 'w') as f:
    print((str(google.results_num) + '個の記事が見つかりました').center(100, '-'))
    for page_results in google.search_results:
        for rst in page_results:
            print(rst.title)
            crawling_text = CrawlingText()
            crawling_text.crawl(rst.url)
            for txt in crawling_text.texts:
                print(fcd.create_corpus(txt))
