from selenium.common.exceptions import TimeoutException

class VideoElement:
    def __init__(self, driver, element):
        self.driver = driver
        self.element = element

    def play(self):
        """播放视频"""
        self.element.click()

    def pause(self):
        """暂停视频"""
        self.element.click()

    def is_playing(self):
        """检查视频是否在播放"""
        return self.element.get_attribute('playing') == 'true'

    def get_duration(self):
        """获取视频总时长"""
        return float(self.element.get_attribute('duration'))

    def get_current_time(self):
        """获取当前播放时间"""
        return float(self.element.get_attribute('currentTime'))

    def seek_to(self, time_in_seconds):
        """跳转到指定时间"""
        self.driver.execute_script(
            'arguments[0].currentTime = arguments[1]',
            self.element,
            time_in_seconds
        )

    def set_volume(self, volume):
        """设置音量 (0-1)"""
        self.driver.execute_script(
            'arguments[0].volume = arguments[1]',
            self.element,
            volume
        )

    def is_muted(self):
        """检查是否静音"""
        return self.element.get_attribute('muted') == 'true'

    def mute(self):
        """静音"""
        self.driver.execute_script(
            'arguments[0].muted = true',
            self.element
        )

    def unmute(self):
        """取消静音"""
        self.driver.execute_script(
            'arguments[0].muted = false',
            self.element
        )

class AudioElement:
    def __init__(self, driver, element):
        self.driver = driver
        self.element = element

    def play(self):
        """播放音频"""
        self.element.click()

    def pause(self):
        """暂停音频"""
        self.element.click()

    def is_playing(self):
        """检查音频是否在播放"""
        return self.element.get_attribute('playing') == 'true'

    def get_duration(self):
        """获取音频总时长"""
        return float(self.element.get_attribute('duration'))

    def get_current_time(self):
        """获取当前播放时间"""
        return float(self.element.get_attribute('currentTime'))

    def seek_to(self, time_in_seconds):
        """跳转到指定时间"""
        self.driver.execute_script(
            'arguments[0].currentTime = arguments[1]',
            self.element,
            time_in_seconds
        )

    def set_volume(self, volume):
        """设置音量 (0-1)"""
        self.driver.execute_script(
            'arguments[0].volume = arguments[1]',
            self.element,
            volume
        )

    def set_playback_rate(self, rate):
        """设置播放速率"""
        self.driver.execute_script(
            'arguments[0].playbackRate = arguments[1]',
            self.element,
            rate
        )

    def wait_for_load(self, timeout=10):
        """等待音频加载完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.element.get_attribute('readyState') == '4':
                return True
            time.sleep(0.5)
        raise TimeoutException("Audio element not loaded") 