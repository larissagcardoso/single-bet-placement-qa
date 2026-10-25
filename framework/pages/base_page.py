"""Explicit-wait helpers shared by every page object. No sleeps, no implicit waits."""
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]


def by_id(element_id: str) -> Locator:
    return (By.ID, element_id)


class BasePage:
    def __init__(self, driver: WebDriver, timeout: float):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def _visible(self, locator: Locator) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _text(self, locator: Locator) -> str:
        return self._visible(locator).text.strip()

    def _click(self, locator: Locator) -> None:
        element = self.wait.until(EC.element_to_be_clickable(locator))
        # Centre the element so the sticky header or the fixed bet slip cannot cover it.
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        element.click()

    def _wait_until_gone(self, locator: Locator) -> None:
        self.wait.until(EC.invisibility_of_element_located(locator))
