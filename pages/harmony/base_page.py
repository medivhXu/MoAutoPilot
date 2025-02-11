from pages.base_page import BasePage
from selenium.webdriver.common.by import By

class HarmonyBasePage(BasePage):
    """鸿蒙系统基础页面类"""
    
    def find_element_by_accessibility_id(self, aid):
        """通过 Accessibility ID 查找元素"""
        return self.driver.find_element_by_accessibility_id(aid)
    
    def find_element_by_hitest(self, hitest_id):
        """通过鸿蒙 HiTest ID 查找元素"""
        return self.driver.find_element(By.ID, f"hitest_{hitest_id}")
    
    def find_element_by_text(self, text):
        """通过文本内容查找元素"""
        return self.driver.find_element(By.XPATH, f"//*[@text='{text}']")