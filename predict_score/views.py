from flask import *
import re
from predict_score.lib.kakaku import KakakuSearcher
from predict_score.lib.searcher import WebPageScraper, Searcher
import pandas as pd
import pickle

app_predict = Blueprint("predict_score", __name__,
                        template_folder="templates", static_folder="./static")

ks = KakakuSearcher()
wps = WebPageScraper()

@app_predict.route("/")
def index():
    values = {}
    return render_template("predict_score/index.html", values=values)

@app_predict.route("/send", methods=["GET", "POST"])
def send():
    values = {"e_cpu": False, "e_gpu": False, "e_ram": False, "e_disk": False, "score": None}
    cpu_url = make_url(request.form["cpu_url"])
    gpu_url = make_url(request.form["gpu_url"])
    ram_url = make_url(request.form["ram_url"])
    disk_url = make_url(request.form["disk_url"])
    cpu_spec = cpu_kakaku(cpu_url)
    if not is_usable_spec(cpu_spec):
        values["e_cpu"] = True
        return render_template("predict_score/index.html", values=values)
    gpu_spec = gpu_kakaku(gpu_url)
    if not is_usable_spec(gpu_spec):
        values["e_gpu"] = True
        return render_template("predict_score/index.html", values=values)
    ram_spec = ram_kakaku(ram_url)
    if not is_usable_spec(ram_spec):
        values["e_ram"] = True
        return render_template("predict_score/index.html", values=values)
    which_disk, disk_spec = disk_kakaku(disk_url)
    if which_disk==None and is_usable_spec(disk_spec):
        values["e_disk"] = True
        return render_template("predict_score/index.html", values=values)
    spec = pd.DataFrame(cpu_spec + gpu_spec + ram_spec + disk_spec).T
    which_disk = "hdd" if which_disk == 0 else "ssd"
    with open("predict_score/data/regression_model_{}.sav".format(which_disk), "rb") as f:
        reg_model = pickle.load(f)
    values["score"] = int(reg_model.predict(spec)[0])

    return render_template("predict_score/index.html", values=values)

def is_usable_spec(spec):
    if not spec:
        return False
    for v in spec:
        if v == None:
            return False
    return True

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
            spec[1] = ks.val_from_item(value, byte="GB") * 1000
        elif title == "メモリバス":
            spec[2] = ks.val_from_item(value)
        elif title == "メモリクロック":
            spec[3] = ks.val_from_item(value) * 1000
    return spec

def ram_kakaku(ram_url):
    page = wps.get_page_source(ram_url)
    vals = ks.value_list(page)
    spec = [None for i in range(2)]
    cap = None
    num = None
    standard = None
    for title, value in vals:
        if title == "メモリ容量(1枚あたり)":
            cap = ks.val_from_item(value, byte="GB")
        elif title == "枚数":
            try:
                num = int(value.replace("枚", ""))
            except:
                continue
        elif title == "メモリ規格":
            standard = value
    if not cap or not num:
        return spec
    if type(standard) == str:
        generation = re.search("DDR(\d)?|SDR", standard, re.IGNORECASE)
        if generation:
            generation = generation.group()
    else:
        generation = None

    if not type(generation) == str:
        generation = None
    elif re.search(r"SDR", generation, re.IGNORECASE):
        generation = 0
    elif re.search(r"DDR$", generation, re.IGNORECASE):
        generation = 1
    elif re.search(r"DDR2", generation, re.IGNORECASE):
        generation = 2
    elif re.search(r"DDR3", generation, re.IGNORECASE):
        generation = 3
    elif re.search(r"DDR4", generation, re.IGNORECASE):
        generation = 4
    elif re.search(r"DDR5", generation, re.IGNORECASE):
        generation = 5
    else:
        generation = None
    return [cap*num, generation]

def disk_kakaku(disk_url):
    page = wps.get_page_source(disk_url)
    vals = ks.value_list(page)
    rpm, cache, read, write = None, None, None, None
    for title, value in vals:
        if title == "回転数":
            rpm = ks.val_from_item(value, byte="GB")
        elif title == "キャッシュ":
            cache = ks.val_from_item(value)
        elif title == "読込速度":
            read = ks.val_from_item(value) /pow(10, 3)
        elif title == "書込速度":
            write = ks.val_from_item(value) /pow(10, 3)
    if rpm and cache:
        return (0, [rpm, cache])
    elif read and write:
        return (1, [read, write])
    else:
        return (None, [None])


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
