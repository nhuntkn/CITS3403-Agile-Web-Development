import pytest

pytestmark = pytest.mark.selenium


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


def test_signup_login_dashboard_and_navigation_in_browser(live_server):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = make_driver()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(f"{live_server}/signup")
        wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys("browseruser")
        driver.find_element(By.NAME, "email").send_keys("browser@example.com")
        driver.find_element(By.NAME, "password").send_keys("Validpass123!")
        driver.find_element(By.NAME, "confirm").send_keys("Validpass123!")
        driver.find_element(By.NAME, "dob").send_keys("01-01-2000")
        driver.find_element(By.NAME, "gender").send_keys("Female")
        driver.find_element(By.NAME, "weight").clear()
        driver.find_element(By.NAME, "weight").send_keys("65")
        driver.find_element(By.NAME, "height").clear()
        driver.find_element(By.NAME, "height").send_keys("170")

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        wait.until(lambda _: submit_button.is_enabled())
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        driver.execute_script("arguments[0].click();", submit_button)

        wait.until(EC.url_contains("/dashboard"))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".main-box")))
        assert "Welcome, browseruser!" in driver.page_source

        driver.get(f"{live_server}/logout")
        wait.until(EC.url_contains("/login"))

        wait.until(EC.visibility_of_element_located((By.ID, "username"))).send_keys("browseruser")
        driver.find_element(By.ID, "password").send_keys("Validpass123!")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        wait.until(EC.url_contains("/dashboard"))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".main-box")))
        assert "Welcome, browseruser!" in driver.page_source

        driver.find_element(By.LINK_TEXT, "Ranking").click()
        wait.until(EC.url_contains("/ranking"))
        assert "Compare users by total calories burned" in driver.page_source

        driver.find_element(By.LINK_TEXT, "History").click()
        wait.until(EC.url_contains("/history"))
        assert "History" in driver.page_source
    finally:
        driver.quit()
