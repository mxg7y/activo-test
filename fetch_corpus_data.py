#! python3
# fetch_corpus_data.py

import re
import time
import urllib
import MeCab
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from collections import namedtuple

SearchResultRow = namedtuple(
    'SearchResultRow',
    ['title', 'url', 'display_url', 'dis']
)

class GoogleScrap():
    def __init__(self, keyword, numpages=3, default_wait=5):
        self.base_url = 'https://www.google.co.jp?pws=0'
        self.keyword = keyword
        self.driver = None
        self.default_wait = default_wait
        self.search_results = [[] for i in range(numpages)]
        self.numpages = numpages
        self.results_num = 0

    def search_with_google(self):
        try:
            self.driver = webdriver.Firefox()
            self.driver.implicitly_wait(self.default_wait)
            self.search_with_keyword()
            for i in range(self.numpages):
                self.get_search(i)
                self.next_page()
        finally:
            self.driver.quit()

    def search_with_keyword(self):
        self.driver.get(self.base_url)
        self.driver.find_element_by_id('lst-ib').send_keys(self.keyword)
        self.driver.find_element_by_id('lst-ib').send_keys(Keys.RETURN)

    def get_search(self, page):
        all_search = self.driver.find_elements_by_class_name('rc')
        for data in all_search:
            title = data.find_element_by_tag_name('h3').text
            url = data.find_element_by_css_selector('h3 > a').get_attribute('href')
            display_url = data.find_element_by_tag_name('cite').text
            try:
                dis = data.find_element_by_class_name('st').text
            except NoSuchElementException:
                dis = ''
            result = SearchResultRow(title, url, display_url, dis)
            self.search_results[page].append(result)
        self.count_results()

    def next_page(self):
        self.driver.find_element_by_css_selector('a#pnnext').click()
        time.sleep(5)

    def count_results(self):
        self.results_num = 0
        for page_results in self.search_results:
            for res in page_results:
                self.results_num += 1

class CrawlingText():
    def __init__(self, default_wait=5):
        self.driver = None
        self.default_wait = default_wait
        self.crawling_urls = []
        self.texts = []

    def crawl(self, url):
        try:
            self.start_driver()
            self.driver.get(url)
            self.get_crawling_urls(url)
            for curl in self.crawling_urls:
                self.get_text(curl)
        finally:
            self.driver.quit()

    def start_driver(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(self.default_wait)

    def get_crawling_urls(self, base_url):
        base_url_parsed = urllib.parse.urlsplit(base_url)
        links = self.driver.find_elements_by_css_selector('a')
        urls = []
        for li in links:
            try:
                url = li.get_attribute('href')
                urls.append(url)
            except:
                continue
        for url in urls:
            url_parsed = urllib.parse.urlsplit(url)
            if base_url_parsed.scheme == url_parsed.scheme and base_url_parsed.netloc == url_parsed.netloc:
                if url not in self.crawling_urls:
                    self.crawling_urls.append(url)

    def get_text(self, url):
        self.driver.get(url)
        body = self.driver.find_element_by_css_selector('body')
        self.texts.append(body.text)

class FormatCorpusData():
    def __init__(self, keyword, window_size=100):
        self.mcb = MeCab.Tagger("-Ochasen")
        self.keyword = keyword
        self.stopword_path = 'stopwords_jp_utf.txt'
        self.stopwords = self.get_stopwords('stopwords_jp_utf.txt')
        self.default_window_size = window_size

    def create_corpus(self, text):
        # 改行をスペース区切りになおす
        text = text.replace('\n', ' ')
        # スペース区切りの文章からワードを抽出
        corpus = self.extract_corpus(text)
        # 形態素解析を行う
        if not corpus: return []
        corpus_sents = []
        for sent in corpus:
            if len(sent) >= self.default_window_size*2:
                former = sent[:self.default_window_size]
                poster = sent[-self.default_window_size:]
                spaced_sent = self.get_morphs(former) + ' ' + self.keyword + ' ' + self.get_morphs(poster)
                corpus_sents.append(spaced_sent)
        return corpus_sents

    def get_stopwords(self, path):
        f = open(path, 'r')
        data = f.read()
        f.close()
        return data.split('\n')

    def extract_corpus(self, text):
        window = r'.{' + str(self.default_window_size) + r'}'
        regex = re.compile(window + self.keyword + window)
        mo = regex.findall(text)
        if len(mo) != 0:
            return mo
        else:
            return []

    def get_morphs(self, text, format='basic', splitter=' '):
        parsed = self.mcb.parse(text)
        parsed = parsed.split('\n')
        morphs = [line.split('\t')[2] for line in parsed if len(line.split('\t')) >= 4]
        return " ".join(morphs)
