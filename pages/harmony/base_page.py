from pages.base_page import BasePage
from selenium.webdriver.common.by import By
from utils.harmony_utils import HarmonyUtils

class HarmonyBasePage(BasePage):
    """鸿蒙系统页面基类"""
    
    def __init__(self, driver):
        super().__init__(driver)
        self.harmony_utils = HarmonyUtils()
    
    def handle_harmony_permissions(self):
        """处理鸿蒙系统的权限弹窗"""
        self.harmony_utils.handle_permissions(self.driver)
    
    def get_harmony_device_info(self):
        """获取鸿蒙设备信息"""
        return self.harmony_utils.get_device_info(self.driver)
    
    def find_element_by_accessibility_id(self, aid):
        """通过 Accessibility ID 查找元素"""
        return self.driver.find_element_by_accessibility_id(aid)
    
    def find_element_by_hitest(self, hitest_id):
        """通过鸿蒙 HiTest ID 查找元素"""
        return self.driver.find_element(By.ID, f"hitest_{hitest_id}")
    
    def find_element_by_text(self, text):
        """通过文本内容查找元素"""
        return self.driver.find_element(By.XPATH, f"//*[@text='{text}']")