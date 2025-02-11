from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from appium.webdriver.common.touch_action import TouchAction
from appium.webdriver.common.multi_action import MultiAction
from appium.webdriver.common.appiumby import AppiumBy
from utils.element_finder import ElementFinder
from utils.media_elements import VideoElement, AudioElement

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self._wait_timeout = 10
        self.element_finder = ElementFinder(self.driver)

    def find_element(self, locator, timeout=None):
        """查找元素"""
        if timeout is None:
            timeout = self._wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            raise TimeoutException(f"Element not found with locator: {locator}")

    def find_elements(self, locator, timeout=None):
        """查找多个元素"""
        if timeout is None:
            timeout = self._wait_timeout
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(locator)
            )
            return elements
        except TimeoutException:
            return []

    # 基础操作
    def click(self, locator):
        """点击元素"""
        element = self.find_element(locator)
        element.click()

    def input_text(self, locator, text):
        """输入文本"""
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)

    def get_text(self, locator):
        """获取元素文本"""
        element = self.find_element(locator)
        return element.text

    def is_element_present(self, locator, timeout=3):
        """判断元素是否存在"""
        try:
            self.find_element(locator, timeout)
            return True
        except TimeoutException:
            return False

    # 手势操作
    def tap(self, x, y, count=1):
        """点击坐标"""
        TouchAction(self.driver).tap(x=x, y=y, count=count).perform()

    def press(self, x, y, duration=1000):
        """长按坐标"""
        TouchAction(self.driver).press(x=x, y=y).wait(duration).release().perform()

    def swipe(self, start_x, start_y, end_x, end_y, duration=None):
        """滑动"""
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def scroll(self, origin_el, destination_el):
        """元素间滚动"""
        self.driver.scroll(origin_el, destination_el)

    def drag_and_drop(self, origin_el, destination_el):
        """拖拽"""
        self.driver.drag_and_drop(origin_el, destination_el)

    # 多点触控
    def pinch(self, element=None):
        """缩小"""
        if element:
            actions = MultiAction(self.driver)
            action1 = TouchAction(self.driver)
            action2 = TouchAction(self.driver)
            
            action1.press(element).move_to(x=10, y=10).wait(1000).release()
            action2.press(element).move_to(x=-10, y=-10).wait(1000).release()
            
            actions.add(action1, action2)
            actions.perform()

    def zoom(self, element=None):
        """放大"""
        if element:
            actions = MultiAction(self.driver)
            action1 = TouchAction(self.driver)
            action2 = TouchAction(self.driver)
            
            action1.press(element).move_to(x=-10, y=-10).wait(1000).release()
            action2.press(element).move_to(x=10, y=10).wait(1000).release()
            
            actions.add(action1, action2)
            actions.perform()

    # 键盘操作
    def hide_keyboard(self):
        """隐藏键盘"""
        self.driver.hide_keyboard()

    def keycode(self, keycode):
        """发送键码"""
        self.driver.press_keycode(keycode)

    # 应用操作
    def background_app(self, seconds):
        """应用切后台"""
        self.driver.background_app(seconds)

    def launch_app(self):
        """启动应用"""
        self.driver.launch_app()

    def close_app(self):
        """关闭应用"""
        self.driver.close_app()

    def reset_app(self):
        """重置应用"""
        self.driver.reset()

    # 上下文切换
    def switch_to_native(self):
        """切换到原生上下文"""
        self.driver.switch_to.context('NATIVE_APP')

    def switch_to_webview(self):
        """切换到 WebView 上下文"""
        available_contexts = self.driver.contexts
        for context in available_contexts:
            if 'WEBVIEW' in context:
                self.driver.switch_to.context(context)
                break

    # 等待方法
    def wait_for_element_visible(self, locator, timeout=None):
        """等待元素可见"""
        if timeout is None:
            timeout = self._wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return element
        except TimeoutException:
            raise TimeoutException(f"Element not visible with locator: {locator}")

    def wait_for_element_clickable(self, locator, timeout=None):
        """等待元素可点击"""
        if timeout is None:
            timeout = self._wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return element
        except TimeoutException:
            raise TimeoutException(f"Element not clickable with locator: {locator}")

    # 截图方法
    def take_screenshot(self, filename):
        """截图"""
        self.driver.get_screenshot_as_file(filename)

    def get_page_source(self):
        """获取页面源码"""
        return self.driver.page_source

    # 设备操作
    def get_device_time(self):
        """获取设备时间"""
        return self.driver.device_time

    def get_device_size(self):
        """获取设备尺寸"""
        return self.driver.get_window_size()

    def set_device_orientation(self, orientation):
        """设置设备方向"""
        self.driver.orientation = orientation

    def open_notifications(self):
        """打开通知栏"""
        self.driver.open_notifications()

    def find_element_smart(self, text=None, id=None):
        """智能查找元素"""
        locator = self.element_finder.get_element_locator(text, id)
        if locator:
            return self.find_element(locator)
        raise Exception(f"Cannot find element with text: {text} or id: {id}")

    def generate_page_elements(self):
        """生成页面元素定位代码"""
        elements = self.driver.find_elements(AppiumBy.XPATH, "//*[@*]")
        
        element_codes = []
        for element in elements:
            attrs = self.element_finder.record_element_attributes(element)
            if attrs.get('text') or attrs.get('resource-id'):
                locator = self.element_finder.generate_locator_code(
                    attrs.get('text'), 
                    attrs.get('resource-id')
                )
                if locator:
                    element_name = attrs.get('text', '').lower().replace(' ', '_')
                    element_codes.append(f"{element_name} = {locator}")
        
        return '\n'.join(element_codes)

    # 多媒体元素处理
    def handle_video(self, video_locator):
        """处理视频元素"""
        video = self.find_element(video_locator)
        return VideoElement(self.driver, video)

    def handle_audio(self, audio_locator):
        """处理音频元素"""
        audio = self.find_element(audio_locator)
        return AudioElement(self.driver, audio)

    # Toast 提示处理
    def get_toast_text(self, partial_text=None, timeout=3):
        """获取 Toast 提示文本
        Args:
            partial_text: Toast 文本的部分内容，用于定位
            timeout: 等待超时时间
        """
        if partial_text:
            locator = (AppiumBy.XPATH, f"//android.widget.Toast[contains(@text,'{partial_text}')]")
        else:
            locator = (AppiumBy.XPATH, "//android.widget.Toast")
        
        try:
            toast = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return toast.get_attribute("text")
        except TimeoutException:
            return None

    def wait_toast_disappear(self, partial_text=None, timeout=3):
        """等待 Toast 消失
        Args:
            partial_text: Toast 文本的部分内容
            timeout: 等待超时时间
        """
        if partial_text:
            locator = (AppiumBy.XPATH, f"//android.widget.Toast[contains(@text,'{partial_text}')]")
        else:
            locator = (AppiumBy.XPATH, "//android.widget.Toast")
            
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def verify_toast(self, expected_text, timeout=3):
        """验证 Toast 提示内容
        Args:
            expected_text: 预期的 Toast 文本
            timeout: 等待超时时间
        """
        actual_text = self.get_toast_text(expected_text, timeout)
        return actual_text and expected_text in actual_text 