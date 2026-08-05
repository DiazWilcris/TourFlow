from selenium.webdriver.common.by import By

from .conftest import create_tour, fill_tour_form, login, submit_without_browser_validation, wait_for, wait_for_message


def test_hu002_crear_gira_exitosamente(driver, live_server):
    create_tour(driver, live_server)
    assert driver.find_element(By.CSS_SELECTOR, "[data-testid='indicator-1']").text == "En progreso"


def test_hu002_no_permite_recaudado_mayor_al_presupuesto(driver, live_server):
    login(driver, live_server)
    driver.find_element(By.ID, "new-tour-button").click()
    wait_for(driver, (By.ID, "tour-form"))
    fill_tour_form(driver, amount_collected="10001")
    submit_without_browser_validation(driver)
    wait_for_message(driver, "El monto recaudado no puede ser mayor que el presupuesto.")


def test_hu002_limite_nombre_cien_caracteres(driver, live_server):
    login(driver, live_server)
    driver.find_element(By.ID, "new-tour-button").click()
    wait_for(driver, (By.ID, "tour-form"))
    fill_tour_form(driver, name="A" * 101)
    submit_without_browser_validation(driver)
    wait_for_message(driver, "El nombre de la gira no puede superar los 100 caracteres.")
