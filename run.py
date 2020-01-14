from flask import *
from suggest_parts.search_max_score import SearchMaxScore

app = Flask("sample")
app.config["DATA_DIR"] = "./data"

@app.route("/")
def index():
    values = {"is_default": True}
    return render_template("index.html", values=values)

@app.route("/send", methods=["GET", "POST"])
def send():
    values = {"is_default": False, "budget":None, "not_found": False, "SCORE":0}
    if request.method == "POST":
        try:
            cap = int(request.form["capacity"])
        except ValueError:
            cap = None
        try:
            budget = int(request.form["budget"])
        except ValueError:
            return render_template("index.html", values=values)
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
        return render_template("index.html", values=values) 
    else:
        return redirect(url_for("index"))

@app.route("/data/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["DATA_DIR"], filename)

if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=False)
