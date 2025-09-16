# flaskai.py
from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from shutil import which
from urllib.parse import quote_plus
import atexit
import time
import os
import traceback

app = Flask(__name__)

# --------------------------
# Create global Selenium driver (reuse browser)
# --------------------------
driver = None

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--incognito")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # ✅ Driver and browser paths
    chrome_driver_path = which("chromedriver") or "/usr/bin/chromedriver"
    chrome_bin_path = (
        which("chromium-browser")
        or which("chromium")
        or "/usr/bin/chromium"
    )

    if not os.path.exists(chrome_driver_path) or not os.path.exists(chrome_bin_path):
        tried = {
            "PATH": os.environ.get("PATH", ""),
            "expected_driver": chrome_driver_path,
            "expected_browser": chrome_bin_path,
            "found_driver": os.path.exists(chrome_driver_path),
            "found_browser": os.path.exists(chrome_bin_path),
        }
        raise Exception("Chromedriver or Chromium not found. Debug: " + repr(tried))

    # Tell selenium where Chromium binary is
    options.binary_location = chrome_bin_path
    service = Service(chrome_driver_path)

    driver_instance = webdriver.Chrome(service=service, options=options)
    driver_instance.set_page_load_timeout(30)

    # Small anti-detection tweak
    try:
        driver_instance.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            """
        })
    except Exception:
        pass

    return driver_instance


def cleanup_driver():
    global driver
    try:
        if driver:
            driver.quit()
    except Exception:
        pass

atexit.register(cleanup_driver)

# --------------------------
# Selenium search runner
# --------------------------
def run_selenium(userq):
    global driver
    try:
        if driver is None:
            driver = create_driver()

        query = quote_plus(userq)
        url = f"https://www.google.com/search?q={query}&hl=en"
        driver.get(url)

        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#search")))
        except TimeoutException:
            pass

        selectors = [
            'div[data-attrid="wa:/description"]',
            'div[data-attrid^="wa:"]',
            'div#search .g .VwiC3b',
            'div#search .g'
        ]

        for sel in selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                if elems and elems[0].text.strip():
                    return elems[0].text.strip()
            except Exception:
                continue

        title = driver.title or ""
        try:
            main = driver.find_element(By.CSS_SELECTOR, "div#search").text
            if main and len(main) < 2000:
                return main.strip()
        except Exception:
            pass

        return title or "No readable result found on the page."

    except Exception as e:
        return f"Selenium error: {str(e)}\n{traceback.format_exc()}"

# --------------------------
# Flask Routes
# --------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    userq = data.get("query")
    if not userq:
        return jsonify({"error": "No query provided"}), 400

    answer = run_selenium(userq)
    return jsonify({"response": answer})

@app.route("/_debug_paths")
def debug_paths():
    info = {
        "PATH": os.environ.get("PATH", ""),
        "chromedriver_exists": os.path.exists("/usr/bin/chromedriver"),
        "chromium_exists": os.path.exists("/usr/bin/chromium-browser"),
        "which_chromedriver": which("chromedriver"),
        "which_chromium": which("chromium-browser"),
    }
    return jsonify(info)

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
