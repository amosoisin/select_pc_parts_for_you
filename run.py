from flask import *
from suggest_parts.search_max_score import SearchMaxScore

app = Flask(__name__)
app.config["DATA_DIR"] = "./data"

@app.route("/")
def index():
    values = {"is_default": True}
    return render_template("index.html", values=values)

@app.route("/send", methods=["GET", "POST"])
def send():
    values = {"is_default": False, "budget":None, "error": False}
    if request.method == "POST":
        try:
            budget = int(request.form["budget"])
        except ValueError:
            return render_template("index.html", values=values)
        try:
            sms = SearchMaxScore(budget)
            sms.search()
            sms.plot_graph()
            suggest_parts = sms.print_max_combi(return_values=True)
            values.update(suggest_parts)
            values["budget"] = budget
        except Exception as e:
            print(e)
            values["error"] = True
            return render_template("index.html", values=values)
        return render_template("index.html", values=values) 
    else:
        return redirect(url_for("index"), values=values)

@app.route("/data/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["DATA_DIR"], filename)

if __name__ == "__main__":
    app.run("0.0.0.0", 80, debug=False)
