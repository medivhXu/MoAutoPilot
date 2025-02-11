from appium.webdriver.common.appiumby import AppiumBy
import yaml
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, WebDriverException

class AppInspector:
    """应用检查器"""
    
    def __init__(self, driver):
        """
        初始化应用检查器
        :param driver: AppiumDriver 实例
        """
        self.driver = driver
        self.page_source = None
        self.element_map = {}

    def get_app_info(self):
        """获取应用基础信息"""
        try:
            app_info = {
                'app_basic': {
                    'package_name': self.driver.current_package,
                    'activity_name': self.driver.current_activity,
                    'platform_version': self.driver.capabilities['platformVersion'],
                    'device_name': self.driver.capabilities['deviceName'],
                    'automation_name': self.driver.capabilities['automationName']
                },
                'app_features': self._scan_app_features()
            }
            return app_info
        except Exception as e:
            print(f"获取应用信息失败: {str(e)}")
            return None

    def _scan_app_features(self):
        """扫描应用功能和界面元素"""
        features = {}
        try:
            # 等待应用加载
            time.sleep(3)
            
            # 获取所有可见元素
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*[@*]")
            
            # 分析界面结构
            current_activity = self.driver.current_activity
            feature_name = current_activity.split('.')[-1].lower()
            
            elements_info = []
            for element in elements:
                try:
                    element_info = {
                        'name': element.get_attribute('content-desc') or element.text or element.tag_name,
                        'type': self._guess_element_type(element),
                        'id': element.get_attribute('resource-id'),
                        'class': element.get_attribute('class'),
                        'clickable': element.get_attribute('clickable'),
                        'bounds': element.get_attribute('bounds')
                    }
                    elements_info.append(element_info)
                except (StaleElementReferenceException, NoSuchElementException):
                    continue

            features[feature_name] = {
                'description': f"{feature_name} 模块",
                'activity': current_activity,
                'elements': elements_info
            }

            # 尝试进行页面导航和扫描其他页面
            self._scan_other_pages(features)

            return features
        except Exception as e:
            print(f"扫描应用功能失败: {str(e)}")
            return {}

    def _guess_element_type(self, element):
        """推测元素类型"""
        class_name = element.get_attribute('class').lower()
        if 'edit' in class_name:
            return 'input'
        elif 'button' in class_name:
            return 'button'
        elif 'image' in class_name:
            return 'image'
        elif 'text' in class_name:
            return 'text'
        elif 'list' in class_name:
            return 'list'
        elif 'video' in class_name:
            return 'video'
        elif 'audio' in class_name:
            return 'audio'
        return 'unknown'

    def _scan_other_pages(self, features):
        """扫描其他页面"""
        try:
            # 查找可点击元素
            clickable_elements = self.driver.find_elements(
                AppiumBy.XPATH, "//*[@clickable='true']")
            
            for element in clickable_elements[:5]:  # 限制扫描深度
                try:
                    # 记录当前页面
                    original_activity = self.driver.current_activity
                    
                    # 点击元素进入新页面
                    element.click()
                    time.sleep(2)
                    
                    # 如果进入了新页面
                    new_activity = self.driver.current_activity
                    if new_activity != original_activity:
                        # 扫描新页面
                        elements = self.driver.find_elements(AppiumBy.XPATH, "//*[@*]")
                        feature_name = new_activity.split('.')[-1].lower()
                        
                        elements_info = []
                        for el in elements:
                            try:
                                element_info = {
                                    'name': el.get_attribute('content-desc') or el.text or el.tag_name,
                                    'type': self._guess_element_type(el),
                                    'id': el.get_attribute('resource-id'),
                                    'class': el.get_attribute('class'),
                                    'clickable': el.get_attribute('clickable'),
                                    'bounds': el.get_attribute('bounds')
                                }
                                elements_info.append(element_info)
                            except (StaleElementReferenceException, NoSuchElementException):
                                continue

                        features[feature_name] = {
                            'description': f"{feature_name} 模块",
                            'activity': new_activity,
                            'elements': elements_info
                        }
                        
                        # 返回上一页
                        self.driver.back()
                        time.sleep(1)
                except (StaleElementReferenceException, NoSuchElementException, WebDriverException):
                    continue
        except Exception as e:
            print(f"扫描其他页面失败: {str(e)}")

    def update_config(self, config_path):
        """更新配置文件"""
        try:
            # 获取应用信息
            app_info = self.get_app_info()
            if not app_info:
                return False

            # 读取现有配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 更新配置
            if 'android' in config:
                config['android'].update({
                    'appPackage': app_info['app_basic']['package_name'],
                    'appActivity': app_info['app_basic']['activity_name']
                })

            # 更新或添加功能描述
            if 'app_features' not in config:
                config['app_features'] = {}
            
            config['app_features'].update(app_info['app_features'])

            # 保存更新后的配置
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            return True
        except Exception as e:
            print(f"更新配置文件失败: {str(e)}")
            return False

    def analyze_current_page(self):
        """
        分析当前页面结构
        :return: 页面元素列表
        """
        self.page_source = self.driver.get_page_source()
        return self._parse_page_source()

    def find_interactive_elements(self):
        """
        查找可交互元素
        :return: 可交互元素列表
        """
        elements = []
        # 查找按钮
        buttons = self.find_elements_by_type('button')
        if buttons:
            elements.extend(buttons)
        
        # 查找输入框
        inputs = self.find_elements_by_type('input')
        if inputs:
            elements.extend(inputs)
        
        # 查找开关
        switches = self.find_elements_by_type('switch')
        if switches:
            elements.extend(switches)
        
        return elements

    def find_elements_by_type(self, element_type):
        """
        根据类型查找元素
        :param element_type: 元素类型
        :return: 元素列表
        """
        try:
            if element_type == 'button':
                return self.driver.find_elements_by_xpath('//*[@type="button" or contains(@class, "button")]')
            elif element_type == 'input':
                return self.driver.find_elements_by_xpath('//*[@type="text" or @type="input"]')
            elif element_type == 'switch':
                return self.driver.find_elements_by_xpath('//*[@type="switch" or contains(@class, "switch")]')
        except Exception as e:
            print(f"查找元素失败: {str(e)}")
            return []

    def generate_element_map(self):
        """
        生成元素地图
        :return: 元素地图字典
        """
        elements = self.find_interactive_elements()
        for element in elements:
            try:
                element_id = element.get_attribute('id') or element.get_attribute('name')
                if element_id:
                    self.element_map[element_id] = {
                        'type': element.get_attribute('type'),
                        'location': element.location,
                        'size': element.size,
                        'text': element.text
                    }
            except Exception as e:
                print(f"处理元素失败: {str(e)}")
        
        return self.element_map 