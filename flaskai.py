# flaskai.py
from flask import Flask, request, jsonify, render_template
from npmai import Ollama
import time
import os


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    


# Example static routes
@app.route("/NPM")
def NPM(): return render_template("NPM.html")
@app.route("/NPMai")
def NPMai(): return render_template("NPMai.html")
@app.route("/NPMboard")
def NPMboard(): return render_template("NPMboard.html")
@app.route("/NPMedu")
def NPMedu(): return render_template("NPMedu.html")
@app.route("/NPMentertainment")
def NPMentertainment(): return render_template("NPMentertainment.html")
@app.route("/NPMfinance")
def NPMfinance(): return render_template("NPMfinance.html")
@app.route("/NPMmap")
def NPMmap(): return render_template("NPMmap.html")
@app.route("/NPMnews")
def NPMnews(): return render_template("NPMnews.html")
@app.route("/NPMstocks")
def NPMstocks(): return render_template("NPMstocks.html")
@app.route("/Sonu")
def Sonu(): return render_template("Sonu.html")
@app.route("/charts")
def charts(): return render_template("charts.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
