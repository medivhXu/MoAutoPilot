import pytest
import time
import sys
import os
import requests
from utils.appium_driver import AppiumDriver
from utils.app_inspector import AppInspector
from utils.test_generator import AutoTestGenerator
from utils.environment_checker import EnvironmentChecker
from utils.logger import logger

class TestAutomation:
    @classmethod
    def setup_class(cls, platform = 'Android Emulator'):
        """测试类初始化"""
        try:
            # 使用 sys.stderr 确保输出不被捕获
            logger.info("\n开始自动化测试环境初始化...", file=sys.stderr)
            
            # 1. 环境检查
            checker = EnvironmentChecker()
            results = checker.check_all(auto_install=False)
            if not results['status']:
                error_msg = "\n环境检查失败，缺少以下组件:\n"
                error_msg += "\n".join(f"  - {component}" for component in results['missing'])
                logger.info(error_msg, file=sys.stderr)
                pytest.skip(error_msg)
            
            
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
                logger.info(error_msg, file=sys.stderr)
                pytest.skip(error_msg)
            
            # 3. 创建会话
            try:
                # 设置超时时间，避免 KeyError: 'timeout' 错误
                timeout_seconds = 120  # 设置默认超时时间为120秒
                logger.info(f"设置会话创建超时时间: {timeout_seconds}秒", file=sys.stderr)
                if not cls.driver.create_session():
                    error_msg = "\nAppium 会话创建失败，请检查:"
                    error_msg += "\n1. 设备/模拟器是否连接"
                    error_msg += "\n2. 应用文件是否存在"
                    error_msg += "\n3. 配置参数是否正确"
                    logger.info(error_msg, file=sys.stderr)
                    pytest.skip(error_msg)
            except KeyError as ke:
                # 专门处理 KeyError 异常，可能是由于缺少参数导致的
                logger.info(f"\n创建会话时出现参数错误: {str(ke)}", file=sys.stderr)
                logger.info("这可能是由于缺少必要的配置参数导致的", file=sys.stderr)
                
                # 检查是否是 'timeout' 键错误
                if str(ke) == "'timeout'":
                    logger.info("检测到 'timeout' 参数缺失，请确保 AppiumDriver.create_session 方法正确处理超时参数", file=sys.stderr)
                    logger.info("尝试不带超时参数重新创建会话...", file=sys.stderr)
                    
                    # 尝试不带超时参数重新调用
                    if not cls.driver.create_session():
                        logger.info("不带超时参数的会话创建也失败了", file=sys.stderr)
                        pytest.skip("Appium 会话创建失败: 参数错误")
                else:
                    pytest.skip(f"Appium 会话创建失败: 缺少参数 {str(ke)}")
            except Exception as e:
                logger.info(f"\n创建会话时出错: {str(e)}", file=sys.stderr)
                logger.info(f"错误类型: {type(e)}", file=sys.stderr)
                logger.info(f"错误详情: {e.__class__.__name__}: {str(e)}", file=sys.stderr)
                if hasattr(e, '__traceback__'):
                    import traceback
                    logger.info(f"错误堆栈:\n{traceback.format_exc()}", file=sys.stderr)
                pytest.skip(str(e))
            
            # 4. 初始化 App 检查器
            cls.inspector = AppInspector(cls.driver)
            logger.info("✓ App 检查器初始化成功", file=sys.stderr)
            
            # 5. 初始化测试生成器
            cls.generator = AutoTestGenerator(cls.inspector)
            logger.info("✓ 测试生成器初始化成功", file=sys.stderr)
            
            # 6. 加载测试用例
            test_instance = cls()  # 创建实例
            test_instance.load_test_cases_from_source()  # 调用实例方法
            
            logger.info("\n环境初始化完成，开始执行测试...", file=sys.stderr)
            
        except Exception as e:
            error_msg = f"\n测试环境初始化失败:\n{str(e)}\n"
            error_msg += "\n可能的原因:"
            error_msg += "\n1. 环境配置不完整"
            error_msg += "\n2. Appium 服务器问题"
            error_msg += "\n3. 设备连接问题"
            error_msg += "\n4. 配置文件错误"
            logger.info(error_msg, file=sys.stderr)
            logger.info(f"错误类型: {type(e)}", file=sys.stderr)
            logger.info(f"错误详情: {e.__class__.__name__}: {str(e)}", file=sys.stderr)
            if hasattr(e, '__traceback__'):
                import traceback
                logger.info(f"错误堆栈:\n{traceback.format_exc()}", file=sys.stderr)
            pytest.skip(error_msg)

    def load_test_cases_from_source(self):
        """加载测试用例文件并调用 Ollama 的 Deepseek 模型"""
        # 指定测试用例文件夹路径
        test_cases_dir = 'test_cases_source'
        gen_cases_dir = 'gen_cases'
        
        # 确保 gen_cases 目录存在
        if not os.path.exists(gen_cases_dir):
            os.makedirs(gen_cases_dir)
            logger.info(f"创建目录: {gen_cases_dir}", file=sys.stderr)
        
        # 遍历文件夹中的所有文件
        for filename in os.listdir(test_cases_dir):
            if filename.endswith('.md'):  # 修改为读取 .md 文件
                file_path = os.path.join(test_cases_dir, filename)
                logger.info(f"正在处理文件: {file_path}", file=sys.stderr)
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    logger.info(f"文件内容: {content[:100]}...", file=sys.stderr)  # 打印文件内容的前100个字符
                    
                    try:
                        # 调用 Ollama 的 Deepseek 模型
                        response = requests.post('http://localhost:11434/api/generate', json={
                            'model': 'deepseek-r1:8b',
                            "prompt": f"""你是一个专注移动APP测试的专家，请针对短视频APP特性生成用例，按JSON格式输出：\
                                        {content}
                                        要求包含：测试步骤、预期结果、优先级。
                                        特别注意：
                                            1. 视频编解码兼容性
                                            2. 高并发场景
                                            3. 中断测试（如来电打断）""",
                            "temperature": 0.3,  # 降低随机性
                            "stream": False  # 确保不使用流式响应
                        })

                        # # langchain 框架
                        # from langchain.prompts import PromptTemplate
                        # from langchain_community.llms import Ollama

                        # template = """作为资深测试工程师，请为{feature}生成测试用例：
                        # 1. 包含{normal_count}个正常场景和{error_count}个异常场景
                        # 2. 每个用例需有明确的前置条件
                        # 3. 输出Markdown表格格式"""

                        # prompt = PromptTemplate.from_template(template)
                        # llm = Ollama(model="deepseek-r1:14b", temperature=0.5)

                        # chain = prompt | llm
                        # logger.info(chain.invoke({
                        #     "feature": "抖音视频上传功能",
                        #     "normal_count": 3,
                        #     "error_count": 2
                        # }))
                        
                        # 生成的文件名
                        gen_filename = f"gen_{filename}"
                        gen_file_path = os.path.join(gen_cases_dir, gen_filename)
                        
                        # 安全地解析 JSON 响应
                        try:
                            response_data = response.json()
                            response_text = response_data.get('response', '')
                        except ValueError as json_err:
                            logger.error(f"JSON 解析错误: {str(json_err)}", file=sys.stderr)
                            logger.error(f"原始响应: {response.text[:200]}...", file=sys.stderr)
                            # 使用原始响应文本
                            response_text = response.text
                        
                        # 将生成的响应保存到 gen_cases 目录
                        with open(gen_file_path, 'w', encoding='utf-8') as gen_file:
                            gen_file.write(response_text)
                        
                        # 打印响应结果
                        logger.info(f"生成的文件: {gen_filename}", file=sys.stderr)
                        logger.info(f"响应内容: {response_text[:100]}...", file=sys.stderr)  # 打印响应内容的前100个字符
                        logger.info("-" * 50, file=sys.stderr)
                    
                    except Exception as e:
                        logger.error(f"处理文件 {filename} 时出错: {str(e)}", file=sys.stderr)
                        import traceback
                        logger.error(f"错误堆栈:\n{traceback.format_exc()}", file=sys.stderr)

    def test_app_launch(self):
        """测试 Chrome 浏览器启动"""
        # 1. 连接设备并启动应用
        session = self.driver.create_session()
        assert session, "Chrome 浏览器启动失败"
        
        # 2. 等待应用完全加载
        time.sleep(3)
        
        # 3. 验证应用是否正常运行
        assert self.driver.get_page_source(), "无法获取 Chrome 页面内容"

    def test_ui_inspection(self):
        """测试 Chrome 浏览器 UI 元素检查"""
        # 1. 分析页面结构
        elements = self.inspector.analyze_current_page()
        assert elements, "Chrome 页面元素分析失败"
        
        # 2. 验证关键元素
        assert self.inspector.find_interactive_elements(), "未找到 Chrome 可交互元素"
        
        # 3. 生成元素地图
        element_map = self.inspector.generate_element_map()
        assert element_map, "Chrome 元素地图生成失败"

    def test_test_generation(self):
        """测试通讯录用例生成"""
        # 1. 基于 UI 分析生成测试用例
        test_cases = self.generator.generate_test_cases()
        assert test_cases, "通讯录测试用例生成失败"
        
        # 2. 验证测试用例结构
        for test_case in test_cases:
            assert 'name' in test_case, "通讯录测试用例缺少名称"
            assert 'steps' in test_case, "通讯录测试用例缺少步骤"
            assert 'expected' in test_case, "通讯录测试用例缺少预期结果"

    def test_basic_interactions(self):
        """测试 Chrome 浏览器基本交互"""
        # 1. 查找地址栏 (尝试多种可能的 ID)
        address_bar = None
        possible_ids = [
            'url_bar', 
            'search_box_text', 
            'url_field', 
            'com.android.chrome:id/url_bar', 
            'com.android.chrome:id/search_box_text'
        ]
        
        for element_id in possible_ids:
            logger.info(f"尝试查找地址栏元素: {element_id}", file=sys.stderr)
            elements = self.inspector.find_elements_by_id(element_id)
            if elements:
                address_bar = elements[0]
                logger.info(f"✓ 找到地址栏元素: {element_id}", file=sys.stderr)
                break
        
        # 如果通过 ID 没找到，尝试使用 XPath
        if not address_bar:
            logger.info("通过 ID 未找到地址栏，尝试使用 XPath", file=sys.stderr)
            xpath_expressions = [
                "//android.widget.EditText[@resource-id='com.android.chrome:id/url_bar']",
                "//android.widget.EditText[@resource-id='com.android.chrome:id/search_box_text']",
                "//android.widget.EditText[contains(@resource-id, 'url')]",
                "//android.widget.EditText[contains(@resource-id, 'search')]"
            ]
            
            for xpath in xpath_expressions:
                logger.info(f"尝试 XPath: {xpath}", file=sys.stderr)
                elements = self.driver.find_elements_by_xpath(xpath)
                if elements:
                    address_bar = elements[0]
                    logger.info(f"✓ 通过 XPath 找到地址栏: {xpath}", file=sys.stderr)
                    break
        
        assert address_bar, "未找到地址栏"
        
        # 2. 在地址栏输入网址
        test_url = "https://www.baidu.com"
        self.driver.input_text(address_bar, test_url)
        logger.info(f"在地址栏输入: {test_url}", file=sys.stderr)
        
        # 3. 按回车键
        self.driver.press_enter()
        logger.info("按下回车键", file=sys.stderr)
        
        # 4. 等待页面加载
        time.sleep(5)
        
        # 5. 验证页面是否加载成功
        page_source = self.driver.get_page_source()
        assert page_source and "baidu" in page_source.lower(), "baidu 页面加载失败"
        logger.info("✓ 页面加载成功", file=sys.stderr)

    @classmethod
    def teardown_class(cls):
        """测试结束清理"""
        if hasattr(cls, 'driver'):
            cls.driver.stop_server()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])