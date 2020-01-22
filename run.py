from flask import *
app = Flask(__name__)

from suggest_parts.views import app_suggest
app.register_blueprint(app_suggest, url_prefix="/suggest_parts")

from predict_score.views import app_predict
app.register_blueprint(app_predict, url_prefix="/predict_score")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
