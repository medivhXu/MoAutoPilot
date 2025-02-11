import pytest
from utils.appium_driver import AppiumDriver
from utils.harmony_utils import HarmonyUtils
from pages.harmony.base_page import HarmonyBasePage

class TestHarmonySpecific:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.driver = AppiumDriver(platform='harmony', check_env=False)
        self.harmony_utils = HarmonyUtils()
        self.base_page = HarmonyBasePage(self.driver)
        yield
        self.driver.quit()

    def test_harmony_features(self):
        """测试鸿蒙特有功能"""
        # 获取设备信息
        device_info = self.harmony_utils.get_device_info(self.driver.driver)
        assert device_info, "无法获取设备信息"
        
        # 测试鸿蒙特有的元素定位方式
        element = self.base_page.find_element_by_hitest("test_id")
        assert element, "无法找到测试元素"