from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .conftest import WAIT_SECONDS, create_tour, fill_tour_form, submit_without_browser_validation, wait_for_message


def test_hu004_editar_gira_exitosamente(driver, live_server):
    create_tour(driver, live_server, name="Gira original", amount_collected="1000")
    driver.find_element(By.ID, "edit-tour-1").click()
    assert driver.find_element(By.ID, "name").get_attribute("value") == "Gira original"
    fill_tour_form(driver, name="Gira actualizada", total_budget="12000", amount_collected="12000")
    driver.find_element(By.ID, "save-tour-button").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains("/dashboard"))
    wait_for_message(driver, "Gira actualizada exitosamente.")
    assert driver.find_element(By.CSS_SELECTOR, "[data-testid='indicator-1']").text == "Financiada"


def test_hu004_editar_rechaza_monto_invalido(driver, live_server):
    create_tour(driver, live_server)
    driver.find_element(By.ID, "edit-tour-1").click()
    fill_tour_form(driver, amount_collected="10001")
    submit_without_browser_validation(driver)
    wait_for_message(driver, "El monto recaudado no puede ser mayor que el presupuesto.")


def test_hu004_editar_limite_nombre(driver, live_server):
    create_tour(driver, live_server)
    driver.find_element(By.ID, "edit-tour-1").click()
    fill_tour_form(driver, name="A" * 101)
    submit_without_browser_validation(driver)
    wait_for_message(driver, "El nombre de la gira no puede superar los 100 caracteres.")
