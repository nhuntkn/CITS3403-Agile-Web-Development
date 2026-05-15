from datetime import date

import pytest

from tests.conftest import create_user

pytestmark = pytest.mark.selenium

VALID_PASSWORD = "Validpass123!"


def make_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1280,900")
        return webdriver.Chrome(service=Service(), options=options)
    except Exception as error:
        pytest.skip(f"Selenium Chrome WebDriver is not available: {error}")


def make_wait(driver):
    from selenium.webdriver.support.ui import WebDriverWait

    return WebDriverWait(driver, 10)


def fill_signup_form(driver, username, email, password=VALID_PASSWORD, confirm=None, fill_email=True):
    from selenium.webdriver.common.by import By

    confirm = password if confirm is None else confirm

    driver.find_element(By.NAME, "username").send_keys(username)
    if fill_email:
        driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "confirm").send_keys(confirm)
    driver.find_element(By.NAME, "dob").send_keys("01-01-2000")
    driver.find_element(By.NAME, "gender").send_keys("Female")
    driver.find_element(By.NAME, "weight").clear()
    driver.find_element(By.NAME, "weight").send_keys("65")
    driver.find_element(By.NAME, "height").clear()
    driver.find_element(By.NAME, "height").send_keys("170")


def click_submit(driver, wait):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    wait.until(lambda _: submit_button.is_enabled())
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    driver.execute_script("arguments[0].click();", submit_button)


def click_add_to_record(driver, wait):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    add_button = driver.find_element(By.ID, "addToRecordBtn")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_button)
    wait.until(EC.element_to_be_clickable((By.ID, "addToRecordBtn")))
    driver.execute_script("arguments[0].click();", add_button)


def signup_user(driver, wait, live_server, username, email, password=VALID_PASSWORD):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from urllib.parse import quote

    driver.get(f"{live_server}/test/set_signup_verified_email?email={quote(email)}")
    driver.get(f"{live_server}/signup")
    wait.until(EC.visibility_of_element_located((By.NAME, "username")))
    fill_signup_form(driver, username, email, password=password, fill_email=False)
    click_submit(driver, wait)
    wait.until(EC.url_contains("/dashboard"))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".main-box")))


def login_user(driver, wait, live_server, username, password=VALID_PASSWORD):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    driver.get(f"{live_server}/login")
    wait.until(EC.visibility_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/dashboard"))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".main-box")))


def add_basic_session(driver, wait, live_server, note="Selenium workout"):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select

    driver.get(f"{live_server}/exercise")
    wait.until(EC.visibility_of_element_located((By.ID, "sessionDate"))).send_keys(date.today().isoformat())
    weight = driver.find_element(By.ID, "weight")
    weight.clear()
    weight.send_keys("70")

    exercise_select = wait.until(EC.visibility_of_element_located((By.ID, "exercise1")))
    Select(exercise_select).select_by_visible_text("Treadmill Walk")
    wait.until(lambda _: len(driver.find_element(By.ID, "level1").find_elements(By.TAG_NAME, "option")) > 1)
    Select(driver.find_element(By.ID, "level1")).select_by_visible_text("3.0 - 3.4 mph")
    driver.find_element(By.ID, "minutes1").send_keys("30")
    driver.find_element(By.NAME, "notes").send_keys(note)

    click_add_to_record(driver, wait)
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".alert-success"), "Session added successfully."))


def test_signup_login_dashboard_and_navigation_in_browser(live_server):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    driver = make_driver()
    wait = make_wait(driver)

    try:
        signup_user(driver, wait, live_server, "browseruser", "browser@example.com")
        assert "Welcome, browseruser!" in driver.page_source

        driver.get(f"{live_server}/logout")
        wait.until(EC.url_contains("/login"))

        login_user(driver, wait, live_server, "browseruser")
        assert "Welcome, browseruser!" in driver.page_source

        driver.find_element(By.LINK_TEXT, "Ranking").click()
        wait.until(EC.url_contains("/ranking"))
        assert "Compare users by total calories burned" in driver.page_source

        driver.find_element(By.LINK_TEXT, "History").click()
        wait.until(EC.url_contains("/history"))
        assert "History" in driver.page_source
    finally:
        driver.quit()


def test_signup_invalid_password_keeps_submit_disabled(live_server):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    driver = make_driver()
    wait = make_wait(driver)

    try:
        driver.get(f"{live_server}/signup")
        wait.until(EC.visibility_of_element_located((By.NAME, "username")))
        fill_signup_form(driver, "weakpassworduser", "weak@example.com", password="short!", confirm="short!")

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        assert not submit_button.is_enabled()
        assert "At least 12 characters" in driver.page_source
    finally:
        driver.quit()


def test_login_invalid_credentials_shows_error(live_server):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    driver = make_driver()
    wait = make_wait(driver)

    try:
        driver.get(f"{live_server}/login")
        wait.until(EC.visibility_of_element_located((By.ID, "username"))).send_keys("missinguser")
        driver.find_element(By.ID, "password").send_keys("wrong-password")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".login-error"), "Invalid username or password"))
        assert "/login" in driver.current_url
    finally:
        driver.quit()


def test_exercise_page_calculates_and_saves_session(live_server):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    driver = make_driver()
    wait = make_wait(driver)

    try:
        signup_user(driver, wait, live_server, "exerciseuser", "exercise@example.com")

        driver.get(f"{live_server}/exercise")
        wait.until(EC.visibility_of_element_located((By.ID, "sessionDate"))).send_keys(date.today().isoformat())
        driver.find_element(By.ID, "weight").clear()
        driver.find_element(By.ID, "weight").send_keys("70")

        from selenium.webdriver.support.ui import Select

        Select(wait.until(EC.visibility_of_element_located((By.ID, "exercise1")))).select_by_visible_text("Treadmill Walk")
        wait.until(lambda _: len(driver.find_element(By.ID, "level1").find_elements(By.TAG_NAME, "option")) > 1)
        Select(driver.find_element(By.ID, "level1")).select_by_visible_text("3.0 - 3.4 mph")
        driver.find_element(By.ID, "minutes1").send_keys("30")

        driver.find_element(By.ID, "calculateCaloriesBtn").click()
        wait.until(EC.text_to_be_present_in_element((By.ID, "result"), "Estimated total calories burnt"))

        click_add_to_record(driver, wait)
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".alert-success"), "Session added successfully."))
    finally:
        driver.quit()


def test_history_delete_removes_saved_session(live_server):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    driver = make_driver()
    wait = make_wait(driver)

    try:
        signup_user(driver, wait, live_server, "historyuser", "history@example.com")
        add_basic_session(driver, wait, live_server, note="Delete me from history")

        driver.get(f"{live_server}/history")
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".history-table"), "Delete me from history"))
        driver.find_element(By.CSS_SELECTOR, "form[action*='/history/'] button[type='submit']").click()
        wait.until(EC.alert_is_present()).accept()

        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".alert-info"), "No exercise sessions saved yet."))
    finally:
        driver.quit()


def test_account_search_finds_existing_user(live_server, app):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    with app.app_context():
        create_user(username="targetuser", email="target@example.com", password=VALID_PASSWORD)

    driver = make_driver()
    wait = make_wait(driver)

    try:
        signup_user(driver, wait, live_server, "accountuser", "account@example.com")

        driver.get(f"{live_server}/account")
        wait.until(EC.visibility_of_element_located((By.ID, "profileSection")))
        driver.find_element(By.XPATH, "//button[normalize-space()='Friend']").click()
        wait.until(EC.visibility_of_element_located((By.ID, "searchInput"))).send_keys("target")
        driver.find_element(By.XPATH, "//button[normalize-space()='Search']").click()

        wait.until(EC.text_to_be_present_in_element((By.ID, "searchResults"), "targetuser"))
        assert "Add" in driver.find_element(By.ID, "searchResults").text
    finally:
        driver.quit()
