from flask import *
from suggest_parts.search_max_score import SearchMaxScore
import threading
import time

app = Flask("sample")
app.config["DATA_DIR"] = "./data"
init_values = {"is_default": False, "budget":None, "not_found": False, "SCORE":0}
values = init_values
dealed = False

class Args:
    cpu_maker = "free"
    gpu_maker = "free"
    hdd_ssd = "free"
    cap = None
    gpu_url = None

@app.route("/")
def index():
    values = {"is_default": True}
    return render_template("index.html", values=values)

@app.route("/send", methods=["GET", "POST"])
def send():
    global dealed
    if request.method == "POST":
        args = Args()
        try:
            args.cap = int(request.form["capacity"])
        except ValueError:
            args.cap = None
        try:
            args.budget = int(request.form["budget"])
        except ValueError:
            return render_template("index.html", values=values)
        args.cpu_maker=request.form["cpu_maker"]
        args.gpu_maker=request.form["gpu_maker"]
        args.hdd_ssd=request.form["hdd_ssd"]
        args.gpu_url=request.form["gpu_url"]
        t = threading.Thread(target=wrapper_run, args=(args, ))
        t.start()
        while True:
            time.sleep(3)
            if dealed:
                dealed = False
                values = init_values
                break
        return render_template("index.html", values=values) 
    else:
        return redirect(url_for("index"))

def wrapper_run(args):
    global dealed
    sms = SearchMaxScore(budget = args.budget,
                         cpu_maker=args.cpu_maker,
                         gpu_maker=args.gpu_maker,
                         hdd_ssd=args.hdd_ssd,
                         minimum_require_capacity=args.cap,
                         gpu_url=args.gpu_url)
    if sms.init_dataset():
        sms.search()
        suggest_parts = sms.print_max_combi(return_values=True)
        values.update(suggest_parts)
        values["budget"] = args.budget
    else:
        values["not_found"] = True
    if values["SCORE"] == 0:
        values["not_found"] = True
    dealed = True

@app.route("/data/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["DATA_DIR"], filename)

if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=False, threaded=True)
