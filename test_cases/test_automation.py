import pytest
import time
import sys
import os
from utils.appium_driver import AppiumDriver
from utils.app_inspector import AppInspector
from utils.test_generator import AutoTestGenerator
from utils.environment_checker import EnvironmentChecker

class TestAutomation:
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        try:
            # 使用 sys.stderr 确保输出不被捕获
            print("\n开始自动化测试环境初始化...", file=sys.stderr)
            
            # 1. 环境检查
            checker = EnvironmentChecker()
            results = checker.check_all(auto_install=False)
            if not results['status']:
                error_msg = "\n环境检查失败，缺少以下组件:\n"
                error_msg += "\n".join(f"  - {component}" for component in results['missing'])
                print(error_msg, file=sys.stderr)
                pytest.skip(error_msg)
            
            # 2. 初始化 Appium 驱动
            platform = os.getenv('TEST_PLATFORM', 'ios')  # 支持从环境变量指定平台
            cls.driver = AppiumDriver(platform=platform, check_env=False)
            
            # 如果是鸿蒙平台，初始化特定工具
            if platform == 'harmony':
                from utils.harmony_utils import HarmonyUtils
                cls.harmony_utils = HarmonyUtils()
                # 处理权限弹窗
                cls.harmony_utils.handle_permissions(cls.driver.driver)
            
            if not cls.driver.start_server():
                error_msg = "\nAppium 服务器启动失败，请检查:"
                error_msg += "\n1. Appium 是否正确安装"
                error_msg += "\n2. 端口是否被占用"
                error_msg += "\n3. 服务器日志输出"
                print(error_msg, file=sys.stderr)
                pytest.skip(error_msg)
            
            # 3. 创建会话
            if not cls.driver.create_session():
                error_msg = "\nAppium 会话创建失败，请检查:"
                error_msg += "\n1. 设备/模拟器是否连接"
                error_msg += "\n2. 应用文件是否存在"
                error_msg += "\n3. 配置参数是否正确"
                print(error_msg, file=sys.stderr)
                pytest.skip(error_msg)
            
            # 4. 初始化 App 检查器
            cls.inspector = AppInspector(cls.driver)
            print("✓ App 检查器初始化成功", file=sys.stderr)
            
            # 5. 初始化测试生成器
            cls.generator = AutoTestGenerator(cls.inspector)
            print("✓ 测试生成器初始化成功", file=sys.stderr)
            
            print("\n环境初始化完成，开始执行测试...", file=sys.stderr)
            
        except Exception as e:
            error_msg = f"\n测试环境初始化失败:\n{str(e)}\n"
            error_msg += "\n可能的原因:"
            error_msg += "\n1. 环境配置不完整"
            error_msg += "\n2. Appium 服务器问题"
            error_msg += "\n3. 设备连接问题"
            error_msg += "\n4. 配置文件错误"
            print(error_msg, file=sys.stderr)
            pytest.skip(error_msg)

    def test_app_launch(self):
        """测试应用启动"""
        # 1. 连接设备并启动应用
        session = self.driver.create_session()
        assert session, "应用启动失败"
        
        # 2. 等待应用完全加载
        time.sleep(3)
        
        # 3. 验证应用是否正常运行
        assert self.driver.get_page_source(), "无法获取页面内容"

    def test_ui_inspection(self):
        """测试 UI 元素检查"""
        # 1. 分析页面结构
        elements = self.inspector.analyze_current_page()
        assert elements, "页面元素分析失败"
        
        # 2. 验证关键元素
        assert self.inspector.find_interactive_elements(), "未找到可交互元素"
        
        # 3. 生成元素地图
        element_map = self.inspector.generate_element_map()
        assert element_map, "元素地图生成失败"

    def test_test_generation(self):
        """测试用例生成"""
        # 1. 基于 UI 分析生成测试用例
        test_cases = self.generator.generate_test_cases()
        assert test_cases, "测试用例生成失败"
        
        # 2. 验证测试用例结构
        for test_case in test_cases:
            assert 'name' in test_case, "测试用例缺少名称"
            assert 'steps' in test_case, "测试用例缺少步骤"
            assert 'expected' in test_case, "测试用例缺少预期结果"

    def test_basic_interactions(self):
        """测试基本交互"""
        # 1. 查找可点击元素
        clickable = self.inspector.find_elements_by_type('clickable')
        assert clickable, "未找到可点击元素"
        
        # 2. 执行点击操作
        element = clickable[0]
        assert self.driver.click_element(element), "点击操作失败"
        
        # 3. 查找输入框
        input_fields = self.inspector.find_elements_by_type('input')
        if input_fields:
            # 4. 执行输入操作
            assert self.driver.input_text(input_fields[0], "测试文本"), "输入操作失败"

    @classmethod
    def teardown_class(cls):
        """测试结束清理"""
        if hasattr(cls, 'driver'):
            cls.driver.stop_server()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])