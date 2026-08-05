from selenium.webdriver.common.by import By

from .conftest import login, wait_for_message


def test_hu001_login_exitoso(driver, live_server):
    login(driver, live_server)
    assert "Dashboard de giras" in driver.page_source


def test_hu001_login_credenciales_incorrectas(driver, live_server):
    driver.get(f"{live_server}/login")
    driver.find_element(By.ID, "username").send_keys("invalido")
    driver.find_element(By.ID, "password").send_keys("incorrecta")
    driver.find_element(By.ID, "login-submit").click()
    wait_for_message(driver, "Credenciales incorrectas.")


def test_hu001_login_limite_usuario_cincuenta_caracteres(driver, live_server):
    driver.get(f"{live_server}/login")
    username = driver.find_element(By.ID, "username")
    driver.execute_script("arguments[0].value = arguments[1];", username, "u" * 51)
    driver.find_element(By.ID, "password").send_keys("cualquier-clave")
    driver.execute_script("document.getElementById('login-form').noValidate = true;")
    driver.find_element(By.ID, "login-submit").click()
    wait_for_message(driver, "Usuario o contraseña incorrectos.")
