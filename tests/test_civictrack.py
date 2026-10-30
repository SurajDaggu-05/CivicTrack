import os
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5000").rstrip("/")
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL", "http://127.0.0.1:4444/wd/hub")
SCREENSHOT_DIR = Path(os.environ.get("SCREENSHOT_DIR", "artifacts"))


def wait_for_http(url, timeout=60):
    deadline, last_error = time.time() + timeout, None
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError, OSError) as error:
            last_error = error
        time.sleep(1)
    raise RuntimeError(f"Endpoint not ready: {url}; last error: {last_error}")


class CivicTrackBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        wait_for_http(f"{APP_URL}/health")
        wait_for_http(SELENIUM_REMOTE_URL.replace("/wd/hub", "/status"))
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        try:
            cls.driver = webdriver.Remote(command_executor=SELENIUM_REMOTE_URL, options=options)
        except WebDriverException as error:
            raise RuntimeError(f"Could not create remote Chrome session: {error}") from error
        cls.driver.set_window_size(1440, 1100)
        cls.wait = WebDriverWait(cls.driver, 15)

    @classmethod
    def tearDownClass(cls):
        driver = getattr(cls, "driver", None)
        if driver is not None:
            driver.quit()

    def setUp(self):
        self.driver.get(APP_URL)

    def test_dashboard_loads_and_health_endpoint_works(self):
        self.assertIn("CivicTrack", self.driver.title)
        self.wait.until(EC.visibility_of_element_located((By.ID, "issue-form")))
        self.assertTrue(self.driver.find_element(By.ID, "count-total").is_displayed())
        self.driver.save_screenshot(str(SCREENSHOT_DIR / "01-dashboard.png"))

    def test_create_issue_update_status_and_persist_after_reload(self):
        unique_title = f"Selenium test issue {int(time.time())}"

        # Fill in the issue report form
        self.driver.find_element(By.ID, "title").send_keys(unique_title)

        Select(
            self.driver.find_element(By.ID, "category")
        ).select_by_visible_text("Road Damage")

        self.driver.find_element(By.ID, "location").send_keys("Test Avenue")

        self.driver.find_element(By.ID, "description").send_keys(
            "Automated browser test: issue lifecycle."
        )

        # Submit the new issue
        submit_button = self.driver.find_element(
            By.CSS_SELECTOR, "#issue-form button[type='submit']"
        )

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            submit_button
        )

        self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#issue-form button[type='submit']")
            )
        ).click()

        # Find the newly created issue card
        xpath = (
            f"//article[contains(@class,'issue-card')]"
            f"[.//h3[normalize-space()='{unique_title}']]"
        )

        card = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )

        self.assertIn("Open", card.text)

        self.driver.save_screenshot(
            str(SCREENSHOT_DIR / "02-issue-created.png")
        )

        # Change the issue status
        status_dropdown = card.find_element(
            By.CSS_SELECTOR, "select[name='status']"
        )

        Select(status_dropdown).select_by_visible_text("In Progress")

        # Scroll to the update button
        update_button = card.find_element(
            By.CSS_SELECTOR, "button[type='submit']"
        )

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            update_button
        )

        # Wait for the specific issue's update button to become clickable
        self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath + "//button[@type='submit']")
            )
        ).click()

        # Verify the status was updated
        card = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )

        self.wait.until(lambda _: "In Progress" in card.text)

        self.driver.save_screenshot(
            str(SCREENSHOT_DIR / "03-status-updated.png")
        )

        # Refresh the page and verify persistence
        self.driver.refresh()

        card = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )

        self.assertIn("In Progress", card.text)

        self.assertTrue(
            self.driver.find_element(By.ID, "count-progress").text.isdigit()
        )

        self.driver.save_screenshot(
            str(SCREENSHOT_DIR / "04-persisted-after-reload.png")
        )

    def test_required_fields_are_present(self):
        for element_id in ("title", "category", "location", "description"):
            self.assertTrue(
                self.driver.find_element(By.ID, element_id).get_attribute("required"),
                f"{element_id} should be required"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
