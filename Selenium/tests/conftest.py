"""Configuración compartida de Selenium, Flask y evidencias HTML."""
import base64
import os
import re
import sys
import threading
import time
from pathlib import Path

import pytest
import pytest_html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from werkzeug.serving import make_server

TEST_DIRECTORY = Path(__file__).resolve().parent
PROJECT_ROOT = (
    TEST_DIRECTORY.parents[1]
    if TEST_DIRECTORY.name == "tests" and TEST_DIRECTORY.parent.name == "Selenium"
    else TEST_DIRECTORY.parent
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app, get_db, init_db

WAIT_SECONDS = 8
CURRENT_CAPTURE_FILES = []


def pytest_collection_modifyitems(items):
    """El reporte siempre se presenta en el orden lógico de las historias."""
    order = {
        "test_login.py": 1,
        "test_crear.py": 2,
        "test_listar.py": 3,
        "test_editar.py": 4,
        "test_eliminar.py": 5,
    }
    items.sort(key=lambda item: (order.get(Path(str(item.fspath)).name, 99), item.location[1]))


def demo_pause(multiplier=1):
    try:
        delay = float(os.getenv("TOURFLOW_STEP_DELAY", "0"))
    except ValueError:
        delay = 0
    if delay > 0:
        time.sleep(delay * multiplier)


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    database = tmp_path_factory.mktemp("tourflow_selenium") / "test.db"
    app.config.update(TESTING=True, DATABASE=str(database), SECRET_KEY="selenium-test-key")
    with app.app_context():
        init_db()
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=3)


@pytest.fixture(autouse=True)
def clean_test_database(live_server):
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM tours")
        db.execute("DELETE FROM sqlite_sequence WHERE name = 'tours'")
        db.commit()


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    if os.getenv("TOURFLOW_HEADLESS") == "1":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    browser = webdriver.Chrome(options=options)
    yield browser
    browser.quit()


@pytest.fixture(autouse=True)
def save_png_evidence(driver, request):
    yield
    try:
        capture_dir = PROJECT_ROOT / "reports" / "capturas"
        capture_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", request.node.name)
        capture_file = capture_dir / f"{safe_name}.png"
        driver.save_screenshot(str(capture_file))
        CURRENT_CAPTURE_FILES.append(capture_file)
    except Exception:
        pass


def wait_for(driver, locator):
    return WebDriverWait(driver, WAIT_SECONDS).until(EC.presence_of_element_located(locator))


def wait_for_message(driver, message):
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-testid='alert-message']"), message)
    )


def login(driver, base_url):
    driver.get(f"{base_url}/login")
    demo_pause()
    wait_for(driver, (By.ID, "username")).send_keys("organizador")
    demo_pause()
    driver.find_element(By.ID, "password").send_keys("TourFlow123!")
    demo_pause()
    driver.find_element(By.ID, "login-submit").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains("/dashboard"))
    demo_pause(2)


def set_date(driver, field, value):
    element = driver.find_element(By.ID, field)
    driver.execute_script(
        "arguments[0].value=arguments[1];"
        "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
        "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
        element, value,
    )


def fill_tour_form(driver, **overrides):
    data = {
        "name": "Gira de prueba", "destination": "Samaná",
        "departure_date": "2026-10-10", "return_date": "2026-10-12",
        "people_count": "30", "total_budget": "10000", "amount_collected": "5000",
        "tour_type": "Escolar", "transport": "Autobús", "status": "Planificada",
    }
    data.update(overrides)
    for field in ("name", "destination", "people_count", "total_budget", "amount_collected"):
        element = driver.find_element(By.ID, field)
        element.clear()
        value = str(data[field])
        if field == "name" and len(value) > 100:
            driver.execute_script("arguments[0].value = arguments[1];", element, value)
        else:
            element.send_keys(value)
        demo_pause()
    set_date(driver, "departure_date", data["departure_date"])
    set_date(driver, "return_date", data["return_date"])
    for field in ("tour_type", "transport", "status"):
        Select(driver.find_element(By.ID, field)).select_by_visible_text(data[field])
        demo_pause()


def create_tour(driver, base_url, **overrides):
    login(driver, base_url)
    driver.find_element(By.ID, "new-tour-button").click()
    wait_for(driver, (By.ID, "tour-form"))
    demo_pause()
    fill_tour_form(driver, **overrides)
    driver.find_element(By.ID, "save-tour-button").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains("/dashboard"))
    wait_for_message(driver, "Gira creada exitosamente.")
    demo_pause(2)


def submit_without_browser_validation(driver):
    driver.execute_script("document.getElementById('tour-form').noValidate = true;")
    driver.find_element(By.ID, "save-tour-button").click()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    driver = item.funcargs.get("driver")
    if driver is None:
        return
    try:
        image_base64 = driver.get_screenshot_as_base64()
        extras = getattr(report, "extras", [])
        extras.append(pytest_html.extras.png(image_base64, name="Captura automática"))
        report.extras = extras
    except Exception:
        pass


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    report_name = getattr(session.config.option, "htmlpath", None)
    if not report_name:
        return
    report_file = Path(report_name)
    capture_dir = PROJECT_ROOT / "reports" / "capturas"
    if not report_file.exists() or not capture_dir.exists():
        return
    try:
        cards = []
        for image_file in CURRENT_CAPTURE_FILES:
            encoded = base64.b64encode(image_file.read_bytes()).decode("ascii")
            title = image_file.stem.replace("_", " ")
            cards.append(
                f'<figure style="margin:16px 0"><figcaption><strong>{title}</strong></figcaption>'
                f'<img alt="{title}" src="data:image/png;base64,{encoded}" '
                'style="max-width:100%;border:1px solid #bbb;margin-top:6px"></figure>'
            )
        if not cards:
            return
        gallery = (
            '<section id="capturas-automaticas" style="padding:20px">'
            '<h2>Capturas automáticas de todos los escenarios</h2>'
            + "".join(cards)
            + "</section>"
        )
        content = report_file.read_text(encoding="utf-8")
        report_file.write_text(content.replace("</body>", gallery + "</body>"), encoding="utf-8")
    except Exception:
        pass
