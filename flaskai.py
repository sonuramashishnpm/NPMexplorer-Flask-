from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from shutil import which
import time
import os
import traceback

app = Flask(__name__)

# --------------------------
# Create global Selenium driver (reuse browser)
# --------------------------
def create_driver():
    options = Options()
    options.add_argument("--headless")               # headless mode for server
    options.add_argument("--no-sandbox")             # required on render
    options.add_argument("--disable-dev-shm-usage")  # avoid memory issues
    options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # auto-detect chromedriver path
    chrome_path = which("chromedriver")
    if not chrome_path:
        raise Exception("Chromedriver not found in PATH!")

    service = Service(chrome_path)
    driver = webdriver.Chrome(service=service, options=options)

    # Anti-detection trick
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })
    return driver


# Keep one global driver instance to reuse across requests
driver = None


def run_selenium(userq):
    global driver
    try:
        if driver is None:
            driver = create_driver()

        url = "https://www.google.com"
        driver.get(url)
        time.sleep(5)

        try:
            aimode = driver.find_element(By.CLASS_NAME, "plR5qb")
            aimode.click()
            time.sleep(3)

            query = driver.find_element(By.CLASS_NAME, "ITIRGe")
            query.clear()
            query.send_keys(userq)
            query.send_keys(Keys.RETURN)

            time.sleep(8)
            result = driver.find_element(By.CLASS_NAME, "pWvJNd").text
        except Exception as e:
            result = f"No result found: {str(e)}"

    except Exception as e:
        result = f"Selenium error: {str(e)}\n{traceback.format_exc()}"

    return result


# --------------------------
# Flask Routes
# --------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    userq = data.get("query")
    if not userq:
        return jsonify({"error": "No query provided"}), 400

    answer = run_selenium(userq)
    return jsonify({"response": answer})


# Example static routes (keep as needed)
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
    app.run(host="0.0.0.0", port=port, debug=True)
