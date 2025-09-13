from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def run_selenium(userq):
    # ---- Setup ----
    options = Options()
    options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    url = "https://www.google.com"
    driver.get(url)
    time.sleep(10)

    try:
        aimode = driver.find_element(By.CLASS_NAME, "plR5qb")
        aimode.click()
        time.sleep(6)

        query = driver.find_element(By.CLASS_NAME, "ITIRGe")
        query.send_keys(userq)
        query.send_keys(Keys.RETURN)

        time.sleep(13)

        result = driver.find_element(By.CLASS_NAME, "pWvJNd").text
    except Exception as e:
        result = f"No result found: {e}"

    driver.quit()
    return result

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/NPM")
def NPM():
    return render_template("NPM.html")
@app.route("/NPMai")
def NPMai():
    return render_template("NPMai.html")
@app.route("/NPMboard")
def NPMboard():
    return render_template("NPMboard.html")
@app.route("/NPMedu")
def NPMedu():
    return render_template("NPMedu.html")
@app.route("/NPMentertainment")
def NPMentertainment():
    return render_template("NPMentertainment.html")
@app.route("/NPMfinance")
def NPMfinance():
    return render_template("NPMfinance.html")
@app.route("/NPMmap")
def NPMmap():
    return render_template("NPMmap.html")
@app.route("/NPMnews")
def NPMnews():
    return render_template("NPMnews.html")
@app.route("/NPMstocks")
def NPMstocks():
    return render_template("NPMstocks.html")
@app.route("/Sonu")
def Sonu():
    return render_template("Sonu.html")
@app.route("/charts")
def charts():
    return render_template("charts.html")
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    userq = data.get("query")
    if not userq:
        return jsonify({"error": "No query provided"}), 400
    
    answer = run_selenium(userq)
    return jsonify({"response": answer})

if __name__ == "__main__":
    app.run(debug=True)
