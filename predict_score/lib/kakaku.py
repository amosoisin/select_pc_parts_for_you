from predict_score.lib.searcher import WebPageScraper
from bs4 import BeautifulSoup
import re

class KakakuSearcher(WebPageScraper):
    def __init__(self):
        super().__init__(use_browser=False)

    def value_list(self, page, add_price_info=True):
        value_list = []
        maker = page.find_all(class_="cateBoxPare")
        if maker:
            maker = maker[2].text
        value_list.append(("maker", maker))
        if add_price_info:
            price = page.find("div", class_="priceWrap")
            if price:
                price = price.find("span", class_="priceTxt").text
                price = int(re.sub(r"¥|,", "", price))
                value_list.append(("price", price))
        table = page.find(class_="tblBorderGray")
        if not table:
            return value_list
        trs = table.find_all("tr")
        for tr in trs:
            th = tr.find_all("th")
            td = tr.find_all("td")
            if not td:
                continue
            for title, value in zip(th, td):
                if value.br:
                    value.br.replace_with("br")
                title = re.sub(r"\s", "", title.text)
                value = re.sub(r"\s", "", value.text).replace("br", " ")
                if not (title and value):
                    continue
                value_list.append((title, value))
        return value_list

    def val_from_item(self, item, byte="KB", hz="GHz", bps="Gbps"):
        """
        Hz:GHz / B:KB / bps:Gbps 
        """
        unit_reg_str = r"(Mbps|Gbps|bit|KB|MB|GB|TB|MHz|GHz|rpm)"
        val_reg_str = r"\d*(\.\d*)?" + unit_reg_str
        val = re.search(val_reg_str, item)
        if not val:
            return None
        val = val.group()
        u = re.search(unit_reg_str, val).group()
        val = float(val.replace(u, ""))
        if re.search("Mbps", u):
            return val / 1000
        elif re.search("MHz", u):
            return val / 1000
        if byte == "KB":
            if re.search("MB", u):
                return val * pow(10, 3)
            elif re.search("GB", u):
                return val * pow(10, 6)
            elif re.search("TB", u):
                return val * pow(10, 9)
        if byte == "GB":
            if re.search("MB", u):
                return val / pow(10, 3)
            elif re.search("TB", u):
                return val * pow(10, 3)
        return val

