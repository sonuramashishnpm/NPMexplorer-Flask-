# flaskai.py
from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from shutil import which
from urllib.parse import quote_plus
import atexit
import time
import os
import traceback

app = Flask(__name__)

# --------------------------
# Helpers: locate executables with multiple fallbacks
# --------------------------
def locate_executable(candidates, fallback_paths):
    # try common binary names first (which)
    for name in candidates:
        path = which(name)
        if path:
            return path
    # try fallback absolute paths
    for p in fallback_paths:
        if os.path.exists(p):
            return p
    return None


# --------------------------
# Create global Selenium driver (reuse browser)
# --------------------------
driver = None

def create_driver():
    # Chrome / Chromium options
    options = Options()
    # use new headless when available; many environments accept this
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--incognito")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # candidate names and fallback locations (extend if needed)
    driver_candidates = ["chromedriver", "chromedriver-stable", "chromium-driver"]
    driver_fallbacks = [
        "/usr/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/lib/chromium/chromedriver",
        "/snap/bin/chromium.chromedriver",
        "/opt/google/chrome/chromedriver"
    ]

    browser_candidates = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"]
    browser_fallbacks = [
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/snap/bin/chromium",
        "/opt/google/chrome/chrome"
    ]

    chrome_driver_path = locate_executable(driver_candidates, driver_fallbacks)
    chrome_bin_path = locate_executable(browser_candidates, browser_fallbacks)

    # helpful debug info if missing
    if not chrome_driver_path or not chrome_bin_path:
        # collect some environment info to help debugging on Render
        tried = {
            "PATH": os.environ.get("PATH", ""),
            "driver_candidates_tried": driver_candidates,
            "driver_fallbacks_tried": driver_fallbacks,
            "browser_candidates_tried": browser_candidates,
            "browser_fallbacks_tried": browser_fallbacks,
            "found_driver": chrome_driver_path,
            "found_browser": chrome_bin_path
        }
        raise Exception("Chromedriver or Chromium not found. See debug info: " + repr(tried))

    # set explicit binary (browser) location
    options.binary_location = chrome_bin_path

    # create service and driver
    service = Service(chrome_driver_path)
    driver_instance = webdriver.Chrome(service=service, options=options)

    # small timeouts & anti-detection
    driver_instance.set_page_load_timeout(30)
    try:
        driver_instance.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            """
        })
    except Exception:
        # ignore if CDP not available
        pass

    return driver_instance


def cleanup_driver():
    global driver
    try:
        if driver:
            driver.quit()
    except Exception:
        pass

# ensure cleanup on process exit
atexit.register(cleanup_driver)


# --------------------------
# Selenium search runner
# --------------------------
from selenium.common.exceptions import TimeoutException

def run_selenium(userq):
    global driver
    try:
        if driver is None:
            driver = create_driver()

        # use direct Google search URL (more stable than clicking homepage UI)
        query = quote_plus(userq)
        url = f"https://www.google.com/search?q={query}&hl=en"
        driver.get(url)

        # wait for the search result container
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#search")))
        except TimeoutException:
            # continue anyway and attempt to extract whatever we can
            pass

        # try a few selectors for featured snippet / main result
        selectors = [
            'div[data-attrid="wa:/description"]',    # featured snippet (sometimes)
            'div[data-attrid^="wa:"]',                # other "wa:" attributes
            'div#search .g .VwiC3b',                  # typical snippet class
            'div#search .g'                           # fallback: first result block
        ]

        for sel in selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                if elems and elems[0].text.strip():
                    return elems[0].text.strip()
            except Exception:
                continue

        # final fallback: page title or an informative message
        title = driver.title or ""
        # also try a last-resort grab of body text in search area
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


# debug route to inspect which binaries were found (useful on Render)
@app.route("/_debug_paths")
def debug_paths():
    driver_candidates = ["chromedriver", "chromedriver-stable", "chromium-driver"]
    driver_fallbacks = [
        "/usr/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/lib/chromium/chromedriver",
        "/snap/bin/chromium.chromedriver",
        "/opt/google/chrome/chromedriver"
    ]
    browser_candidates = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"]
    browser_fallbacks = [
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/snap/bin/chromium",
        "/opt/google/chrome/chrome"
    ]
    found_driver = locate_executable(driver_candidates, driver_fallbacks)
    found_browser = locate_executable(browser_candidates, browser_fallbacks)
    info = {
        "PATH": os.environ.get("PATH", ""),
        "found_chromedriver": found_driver,
        "found_chromium": found_browser,
        "driver_candidates": driver_candidates,
        "driver_fallbacks": driver_fallbacks,
        "browser_candidates": browser_candidates,
        "browser_fallbacks": browser_fallbacks
    }
    return jsonify(info)


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
    # set debug=False for deploy (prevents Flask reloader spawning multiple processes)
    app.run(host="0.0.0.0", port=port, debug=False)
