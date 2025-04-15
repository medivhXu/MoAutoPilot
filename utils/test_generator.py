import os
from jinja2 import Template
from utils.logger import logger

class AutoTestGenerator:  # 改名以避免与测试类混淆
    """测试用例生成器"""
    
    def __init__(self, inspector):
        """
        初始化测试生成器
        :param inspector: AppInspector 实例
        """
        self.inspector = inspector
        self.test_cases = []

    def generate_test_cases(self):
        """
        生成测试用例
        :return: 测试用例列表
        """
        try:
            # 获取当前页面元素
            elements = self.inspector.analyze_current_page()
            if not elements:
                logger.warning("未找到页面元素，使用默认测试用例")
                # 返回默认测试用例
                return [
                    {
                        'name': 'Chrome 浏览器基本功能测试',
                        'steps': [
                            '1. 打开 Chrome 浏览器',
                            '2. 在地址栏输入网址',
                            '3. 点击回车键访问网站'
                        ],
                        'expected': '网站成功加载并显示'
                    },
                    {
                        'name': 'Chrome 浏览器书签功能测试',
                        'steps': [
                            '1. 打开 Chrome 浏览器',
                            '2. 访问网站',
                            '3. 点击菜单按钮',
                            '4. 点击星形图标添加书签'
                        ],
                        'expected': '成功添加书签并显示确认消息'
                    }
                ]
            
            # 基于页面元素生成测试用例
            test_cases = []
            
            # 分析可交互元素
            interactive_elements = self.inspector.find_interactive_elements()
            
            # 为每个可交互元素生成测试用例
            for i, element in enumerate(interactive_elements):
                element_type = element.get('attributes', {}).get('class', '未知类型')
                element_text = element.get('text', '').strip() or f"元素 {i+1}"
                
                test_case = {
                    'name': f"测试 {element_text} ({element_type})",
                    'steps': [
                        '1. 打开 Chrome 浏览器',
                        f'2. 定位 {element_text} 元素',
                        f'3. 点击 {element_text} 元素'
                    ],
                    'expected': f'{element_text} 元素响应点击并执行相应操作'
                }
                test_cases.append(test_case)
            
            logger.info(f"生成了 {len(test_cases)} 个测试用例")
            return test_cases
        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}")
            # 返回一个默认测试用例，避免返回空列表
            return [{
                'name': 'Chrome 浏览器默认测试',
                'steps': ['1. 打开 Chrome 浏览器', '2. 验证浏览器是否正常启动'],
                'expected': 'Chrome 浏览器成功启动并显示主页'
            }]

    def _create_test_case(self, element):
        """
        为单个元素创建测试用例
        :param element: UI 元素
        :return: 测试用例字典
        """
        element_info = {
            'type': element.get('type', 'unknown'),
            'name': element.get('name') or element.get('text') or '未命名元素'
        }
        
        test_case = {
            'name': f'测试_{element_info["type"]}_{element_info["name"]}',
            'steps': [],
            'expected': []
        }
        
        # 根据元素类型生成测试步骤
        if element_info['type'] == 'button':
            test_case['steps'].append(f'点击 {element_info["name"]} 按钮')
            test_case['expected'].append('按钮点击成功')
        
        elif element_info['type'] == 'input':
            test_case['steps'].extend([
                f'找到 {element_info["name"]} 输入框',
                '输入测试文本',
                '验证输入内容'
            ])
            test_case['expected'].append('输入内容与预期一致')
        
        elif element_info['type'] == 'switch':
            test_case['steps'].append(f'切换 {element_info["name"]} 开关状态')
            test_case['expected'].append('开关状态改变')
        
        return test_case

    def _generate_module_tests(self, module, info):
        """生成模块测试用例"""
        template = self._get_template(module)
        return template.render(
            module=module,
            description=info['description'],
            elements=info['elements'],
            **self._get_extra_context(info)
        )
    
    def _get_template(self, module):
        """获取测试用例模板"""
        templates = {
            'login': Template('''
from utils.appium_driver import AppiumDriver
from pages.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy
import pytest

class Test{{ module|title }}:
    def setup_class(self):
        self.driver = AppiumDriver().init_driver()
        self.page = BasePage(self.driver)

    def teardown_class(self):
        self.driver.quit()

    {% for element in elements %}
    def test_{{ element.name|lower|replace(" ", "_") }}(self):
        """测试{{ element.name }}"""
        {% if element.type == "input" %}
        self.page.input_text((AppiumBy.ID, "{{ element.id }}"), "test_input")
        {% elif element.type == "button" %}
        self.page.click((AppiumBy.ID, "{{ element.id }}"))
        {% endif %}
        
    {% endfor %}

    {% if validations %}
    @pytest.mark.parametrize("test_input,expected", [
        {% for validation in validations %}
        ("{{ validation }}", "{{ validation }}提示"),
        {% endfor %}
    ])
    def test_validations(self, test_input, expected):
        """测试验证提示"""
        # 触发验证
        self.page.click((AppiumBy.ID, "login_button"))
        # 验证提示
        assert self.page.verify_toast(expected)
    {% endif %}
'''),
            'home': Template('''
from utils.appium_driver import AppiumDriver
from pages.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy

class Test{{ module|title }}:
    def setup_class(self):
        self.driver = AppiumDriver().init_driver()
        self.page = BasePage(self.driver)

    def teardown_class(self):
        self.driver.quit()

    {% for element in elements %}
    def test_{{ element.name|lower|replace(" ", "_") }}(self):
        """测试{{ element.name }}"""
        {% if element.type == "search" %}
        self.page.input_text((AppiumBy.ID, "{{ element.id }}"), "搜索关键词")
        {% elif element.type == "swipe" %}
        # 获取轮播容器
        banner = self.page.find_element((AppiumBy.ID, "{{ element.id }}"))
        # 左右滑动
        self.page.swipe(banner.location['x'], banner.location['y'],
                       banner.location['x'] + 200, banner.location['y'])
        {% elif element.type == "list" %}
        # 获取列表元素
        products = self.page.find_elements((AppiumBy.ID, "{{ element.id }}"))
        assert len(products) > 0
        {% endif %}
        
    {% endfor %}

    {% if gestures %}
    {% for gesture in gestures %}
    def test_{{ gesture|lower|replace(" ", "_") }}(self):
        """测试{{ gesture }}"""
        {% if "下拉" in gesture %}
        # 下拉刷新
        self.page.swipe(200, 200, 200, 400)
        {% elif "上拉" in gesture %}
        # 上拉加载
        self.page.swipe(200, 400, 200, 200)
        {% endif %}
    {% endfor %}
    {% endif %}
'''),
            'product_detail': Template('''
from utils.appium_driver import AppiumDriver
from pages.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy

class Test{{ module|title }}:
    def setup_class(self):
        self.driver = AppiumDriver().init_driver()
        self.page = BasePage(self.driver)

    def teardown_class(self):
        self.driver.quit()

    {% for element in elements %}
    def test_{{ element.name|lower|replace(" ", "_") }}(self):
        """测试{{ element.name }}"""
        {% if element.type == "gallery" %}
        gallery = self.page.find_element((AppiumBy.ID, "{{ element.id }}"))
        # 左右滑动查看图片
        self.page.swipe(gallery.location['x'], gallery.location['y'],
                       gallery.location['x'] + 200, gallery.location['y'])
        {% elif element.type == "button" %}
        self.page.click((AppiumBy.ID, "{{ element.id }}"))
        {% endif %}
        
    {% endfor %}

    {% if media %}
    {% for item in media %}
    def test_{{ item.name|lower|replace(" ", "_") }}(self):
        """测试{{ item.name }}"""
        {% if item.type == "video" %}
        video = self.page.handle_video((AppiumBy.ID, "{{ item.id }}"))
        video.play()
        assert video.is_playing()
        video.pause()
        {% elif item.type == "audio" %}
        audio = self.page.handle_audio((AppiumBy.ID, "{{ item.id }}"))
        audio.play()
        assert audio.is_playing()
        audio.pause()
        {% endif %}
    {% endfor %}
    {% endif %}
''')
        }
        return templates.get(module)
    
    def _get_extra_context(self, info):
        """获取额外的模板上下文"""
        context = {}
        if 'validations' in info:
            context['validations'] = info['validations']
        if 'gestures' in info:
            context['gestures'] = info['gestures']
        if 'media' in info:
            context['media'] = info['media']
        return context

    def save_test_cases(self, output_dir='test_cases'):
        """保存生成的测试用例"""
        os.makedirs(output_dir, exist_ok=True)
        
        test_cases = self.generate_test_cases()
        for module, content in test_cases.items():
            with open(os.path.join(output_dir, f'test_{module}.py'), 'w', encoding='utf-8') as f:
                f.write(content)