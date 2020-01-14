from selenium import webdriver
from urllib import parse
from bs4 import BeautifulSoup
from urllib import request

class WebPageScraper:
    def __init__(self, use_browser=False):
        self.use_browser = use_browser
        if self.use_browser:
            self.browser = self.set_firefox_browser()

    def set_firefox_browser(self):
        profile = webdriver.FirefoxProfile()
        options = webdriver.firefox.options.Options()
        options.add_argument("--headless")
        browser = webdriver.Firefox(firefox_profile=profile,
                                    firefox_options=options)
        return browser

    def get_page_source(self, url):
        page_source = None
        for i in range(10):
            try:
                if self.use_browser:
                    self.browser.get(url)
                    page_source = self.browser.page_source
                else:
                    page_source = request.urlopen(url).read()
            except Exception as e:
                print(e)
                continue
            break
        if not page_source:
            return None
        return BeautifulSoup(page_source, "lxml")

    def quit(self):
        if self.use_browser:
            self.browser.quit()
        else:
            pass


class Searcher(WebPageScraper):
    def __init__(self, use_tor=False):
        super().__init__(use_browser=True)
        self.engine = "https://duckduckgo.com/?"

    def result_page(self, word, addition_word=None):
        page_list = []
        word = word+ addition_word if addition_word else word
        query = parse.urlencode({"q":word, "kl":"jp-jp"})
        results = self.get_page_source(self.engine+query)
        class_name = "result__a"
        results = results.find_all(class_=class_name)
        for result in results:
            result = result.get("href")
            if result:
                page_list.append(str(result))
        return page_list
