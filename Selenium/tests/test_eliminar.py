from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .conftest import WAIT_SECONDS, create_tour, login, wait_for_message


def test_hu005_eliminar_gira_confirmando(driver, live_server):
    create_tour(driver, live_server)
    driver.find_element(By.ID, "delete-tour-1").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.alert_is_present()).accept()
    wait_for_message(driver, "Gira eliminada exitosamente.")
    assert driver.find_element(By.ID, "empty-state").text == "No hay registros disponibles."


def test_hu005_cancelar_eliminacion_conserva_gira(driver, live_server):
    create_tour(driver, live_server)
    driver.find_element(By.ID, "delete-tour-1").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.alert_is_present()).dismiss()
    assert "Gira de prueba" in driver.page_source


def test_hu005_gira_inexistente_muestra_mensaje(driver, live_server):
    login(driver, live_server)
    driver.get(f"{live_server}/tours/999/edit")
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains("/dashboard"))
    wait_for_message(driver, "Gira no encontrada.")
