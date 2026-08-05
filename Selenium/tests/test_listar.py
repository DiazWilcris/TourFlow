from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .conftest import WAIT_SECONDS, create_tour, fill_tour_form, login, wait_for, wait_for_message


def test_hu003_dashboard_lista_giras(driver, live_server):
    create_tour(driver, live_server, name="Gira Norte")
    driver.find_element(By.ID, "new-tour-button").click()
    wait_for(driver, (By.ID, "tour-form"))
    fill_tour_form(driver, name="Gira Sur", destination="Barahona")
    driver.find_element(By.ID, "save-tour-button").click()
    wait_for_message(driver, "Gira creada exitosamente.")
    assert len(driver.find_elements(By.CSS_SELECTOR, "tbody tr")) == 2


def test_hu003_busqueda_sin_resultados(driver, live_server):
    create_tour(driver, live_server)
    driver.find_element(By.ID, "search-input").send_keys("NoExiste")
    driver.find_element(By.ID, "search-button").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains("q=NoExiste"))
    empty_message = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.presence_of_element_located((By.ID, "empty-search"))
    )
    assert empty_message.text == "No se encontraron resultados."


def test_hu003_dashboard_requiere_autenticacion(driver, live_server):
    driver.get(f"{live_server}/dashboard")
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains("/login"))
    wait_for_message(driver, "Debes iniciar sesión para acceder.")
