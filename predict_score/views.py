from flask import *
import re
from predict_score.lib.kakaku import KakakuSearcher
from predict_score.lib.searcher import WebPageScraper, Searcher

app_predict = Blueprint("predict_score", __name__,
                        template_folder="templates", static_folder="./static")

ks = KakakuSearcher()
wps = WebPageScraper()

@app_predict.route("/")
def index():
    return render_template("predict_score/index.html")

@app_predict.route("/send", methods=["GET", "POST"])
def send():
    cpu_url = make_url(request.form["cpu_url"])
    gpu_url = make_url(request.form["gpu_url"])
    ram_url = make_url(request.form["ram_url"])
    disk_url = make_url(request.form["disk_url"])
    cpu_spec = cpu_kakaku(cpu_url)
    gpu_spec = gpu_kakaku(gpu_url)
    print(gpu_spec)

    return render_template("predict_score/index.html")

def cpu_kakaku(cpu_url):
    page = wps.get_page_source(cpu_url)
    if not page:
        return None
    vals = ks.value_list(page)
    maker = None
    cache_3 = None
    smart_cache = None
    spec = [None for i in range(9)]
    for title, value in vals:
        if title == "プロセッサ名":
            name = value
        elif title == "maker":
            maker = value
        elif title == "クロック周波数":
            spec[0] = ks.val_from_item(value)
        elif title == "コア数":
            spec[1] = int(value.replace("コア", ""))
        elif title == "スレッド数":
            spec[2] = int(value)
        elif title == "二次キャッシュ":
            spec[3] = 1
            spec[4] = ks.val_from_item(value)
        elif title == "三次キャッシュ":
            cache_3 = ks.val_from_item(value)
    if not spec[4]:
        spec[3] = 0
        spec[4] = 0
    if maker == 'インテル':
        s = Searcher()
        intel_url = pageFilter(s.result_page(name, "ark.intel"))
        s.quit()
        if intel_url:
            intel_url = intel_url[0]
            smart_cache = findSpecFromIntel(intel_url)
        spec[5] = 0 if smart_cache else 1
        spec[6] = 0 if smart_cache else cache_3
        spec[7] = 1 if smart_cache else 0
        spec[8] = smart_cache if smart_cache else 0
    else:
        spec[5] = 1 if cache_3 else 0
        spec[6] = cache_3 if cache_3 else 0
        spec[7] = 0
        spec[8] = 0
    return spec

def gpu_kakaku(gpu_url):
    page = wps.get_page_source(gpu_url)
    vals = ks.value_list(page)
    spec = [None for i in range(4)]
    for title, value in vals:
        if title == "SP数" or title == "CUDAコア数":
            spec[0] = int(value)
        elif title == "メモリ":
            spec[1] = ks.val_from_item(value, byte="MB")
        elif title == "メモリバス":
            spec[2] = ks.val_from_item(value)
        elif title == "メモリクロック":
            spec[3] = ks.val_from_item(value) * 1000
    return spec

def findSpecFromIntel(url):
    result_page = wps.get_page_source(url)
    if not result_page:
        return None
    cache = result_page.find(attrs={"data-key":"Cache"})
    if cache:
        cache = cache.text.replace(" ", "").replace("\n", "")
        cache_type = re.search("L2|L3|SmartCache", cache)
        if not cache_type:
            return None
        cache_type = cache_type.group()
        val = ks.val_from_item(cache)
        if re.search("SmartCache", cache_type):
            return val
        else:
            return None

def pageFilter(page_list):
    search_list = []
    intel_page = re.compile(r"https://ark.intel.com/content/www/(us|jp)/(en|ja)/ark/products/(\d+)")
    for page in page_list:
        if intel_page.search(page):
            search_list.append(page)
    return search_list

def make_url(text):
    code_compile = re.compile(r"K\d+")
    url_format = "https://kakaku.com/item/{}/spec/"
    url = code_compile.search(text)
    url = url_format.format(url.group()) if url else None
    return url
