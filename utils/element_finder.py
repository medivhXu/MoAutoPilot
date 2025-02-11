from appium.webdriver.common.appiumby import AppiumBy
import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

class ElementFinder:
    def __init__(self, driver):
        self.driver = driver

    def get_element_locator(self, element_text=None, element_id=None, timeout=5):
        """自动获取元素定位方式"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            locator_strategies = {
                'accessibility_id': (AppiumBy.ACCESSIBILITY_ID, element_text),
                'id': (AppiumBy.ID, element_id or element_text),
                'xpath_text': (AppiumBy.XPATH, f"//*[@text='{element_text}']"),
                'xpath_contains': (AppiumBy.XPATH, f"//*[contains(@text,'{element_text}')]"),
                'class_name': (AppiumBy.CLASS_NAME, element_text),
            }

            for strategy, locator in locator_strategies.items():
                try:
                    element = self.driver.find_element(locator[0], locator[1])
                    if element.is_displayed():
                        return locator
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            time.sleep(0.5)
        return None

    def record_element_attributes(self, element):
        """记录元素的所有可用属性"""
        attributes = {}
        try:
            attributes['text'] = element.text
            attributes['content-desc'] = element.get_attribute('content-desc')
            attributes['resource-id'] = element.get_attribute('resource-id')
            attributes['class'] = element.get_attribute('class')
            attributes['package'] = element.get_attribute('package')
            attributes['bounds'] = element.get_attribute('bounds')
        except (StaleElementReferenceException, NoSuchElementException):
            pass
        return attributes

    def generate_locator_code(self, element_text=None, element_id=None):
        """生成定位代码"""
        locator = self.get_element_locator(element_text, element_id)
        if locator:
            return f"({locator[0]}, '{locator[1]}')"
        return None 