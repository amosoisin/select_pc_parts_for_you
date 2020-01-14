from flask import *
from suggest_parts.search_parts_combi.search_max_score import SearchMaxScore
import pickle

app_suggest = Blueprint("suggest_parts", __name__,
                        template_folder="templates", static_folder="./static")
with open("data/examples.dict", "rb") as f:
    examples = pickle.load(f)

@app_suggest.route("/")
def index():
    values = {"is_default": True, "examples": examples}
    return render_template("suggest_parts/index.html", values=values)

@app_suggest.route("/send", methods=["GET", "POST"])
def send():
    values = {"is_default": False, "budget":None, "not_found": False, "SCORE":0, "examples": examples}
    if request.method == "POST":
        try:
            cap = int(request.form["capacity"])
        except ValueError:
            cap = 0
        try:
            budget = int(request.form["budget"]) * 10000
        except ValueError:
            return render_template("suggest_parts/index.html", values=values)
        sms = SearchMaxScore(budget,
                             cpu_maker=request.form["cpu_maker"],
                             gpu_maker=request.form["gpu_maker"],
                             hdd_ssd=request.form["hdd_ssd"],
                             minimum_require_capacity=cap,
                             gpu_url=request.form["gpu_url"])
        if sms.init_dataset():
            sms.search()
            suggest_parts = sms.print_max_combi(return_values=True)
            values.update(suggest_parts)
            values["budget"] = budget
        else:
            values["not_found"] = True
        if values["SCORE"] == 0:
            values["not_found"] = True
        return render_template("suggest_parts/index.html", values=values) 
    else:
        return redirect(url_for("suggest_parts.index"))
