from appium import webdriver
import yaml
import os
from utils.app_inspector import AppInspector
from utils.environment_checker import EnvironmentChecker
import subprocess
import time
import sys

class AppiumDriver:
    def __init__(self, platform='ios', check_env=True):
        self.platform = platform.lower()
        # 添加鸿蒙 OS 平台支持
        if self.platform not in ['ios', 'android', 'harmony']:
            raise ValueError("Platform must be 'ios', 'android' or 'harmony'")
        
        self.capabilities = {
            'ios': {
                'platformName': 'iOS',
                'automationName': 'XCUITest'
            },
            'android': {
                'platformName': 'Android',
                'automationName': 'UiAutomator2'
            },
            'harmony': {
                'platformName': 'HarmonyOS',
                'automationName': 'HarmonyDriver',
                'noReset': True
            }
        }
        self.driver = None
        self.platform = platform.lower()
        self.server_process = None
        
        # 环境检查
        if check_env:
            checker = EnvironmentChecker()
            results = checker.check_all()
            if not results['status']:
                checker.print_report()
                raise EnvironmentError("环境配置不完整，请按建议进行安装配置")
        
        print(f"\n初始化 {platform.upper()} 测试环境...", file=sys.stderr)
        
        # 加载配置
        try:
            self.config = self._load_config()
            print("✓ 配置文件加载成功", file=sys.stderr)
        except Exception as e:
            print(f"✗ 配置文件加载失败: {str(e)}", file=sys.stderr)
            raise
        
        # 设置 Appium 服务器地址
        self.appium_host = self.config.get('appium_server', {}).get('host') or os.getenv('APPIUM_HOST', 'localhost')
        self.appium_port = self.config.get('appium_server', {}).get('port') or os.getenv('APPIUM_PORT', '4723')
        print(f"✓ Appium 服务器地址: {self.appium_host}:{self.appium_port}")

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def start_server(self):
        """启动 Appium 服务器"""
        print("\n启动 Appium 服务器...")
        try:
            # 检查 Appium 是否已安装
            result = subprocess.run(['appium', '-v'], capture_output=True, text=True)
            print(f"✓ Appium 版本: {result.stdout.strip()}")
            
            # 检查端口是否被占用
            if self._is_port_in_use(self.appium_port):
                print(f"✗ 端口 {self.appium_port} 已被占用")
                return False
            
            # 启动 Appium 服务器
            cmd = ['appium', '--address', self.appium_host, '--port', self.appium_port]
            self.server_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(5)  # 等待服务器启动
            
            # 检查服务器是否成功启动
            if self.server_process.poll() is None:
                print("✓ Appium 服务器启动成功")
                return True
            else:
                error = self.server_process.stderr.read()
                print(f"✗ Appium 服务器启动失败: {error}")
                return False
        except Exception as e:
            print(f"✗ 启动 Appium 服务器失败: {str(e)}")
            return False

    def _is_port_in_use(self, port):
        """检查端口是否被占用"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', int(port))) == 0

    def create_session(self):
        """创建 Appium 会话"""
        print("\n创建 Appium 会话...")
        try:
            # 获取平台特定的配置
            caps = self.config[self.platform].copy()
            print(f"✓ 已加载 {self.platform} 平台配置")
            
            # 检查必要的配置项
            required_caps = ['deviceName', 'platformVersion', 'app']
            missing_caps = [cap for cap in required_caps if not caps.get(cap)]
            if missing_caps:
                print(f"✗ 缺少必要的配置项: {', '.join(missing_caps)}")
                return None
            
            # 添加通用配置
            caps.update({
                'platformName': self.platform.capitalize(),
                'automationName': 'XCUITest' if self.platform == 'ios' else 'UiAutomator2',
                'noReset': True
            })
            
            # 检查应用文件是否存在
            app_path = os.path.expanduser(caps['app'])
            if not os.path.exists(app_path):
                print(f"✗ 应用文件不存在: {app_path}")
                return None
            caps['app'] = app_path
            
            # 连接 Appium 服务器
            server_url = f'http://{self.appium_host}:{self.appium_port}/wd/hub'
            print(f"✓ 正在连接服务器: {server_url}")
            
            self.driver = webdriver.Remote(server_url, caps)
            self.driver.implicitly_wait(self.config['test_info']['implicit_wait'])
            print("✓ Appium 会话创建成功")
            
            return self.driver
        except Exception as e:
            print(f"✗ 创建 Appium 会话失败: {str(e)}")
            return None

    def stop_server(self):
        """停止 Appium 服务器"""
        if self.driver:
            self.driver.quit()
        if self.server_process:
            self.server_process.terminate()

    def init_driver(self):
        """初始化 Appium driver"""
        try:
            if self.platform.lower() == 'android':
                caps = self.config['android']
            else:
                caps = self.config['ios']

            # 使用环境变量中的 Appium 服务器地址
            server_url = f'http://{self.appium_host}:{self.appium_port}/wd/hub'
            self.driver = webdriver.Remote(server_url, caps)
            self.driver.implicitly_wait(self.config['test_info']['implicit_wait'])
            
            # 自动获取应用信息并更新配置
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
            inspector = AppInspector(self.driver)
            inspector.update_config(config_path)
            
            return self.driver
        except Exception as e:
            raise Exception(f"Failed to initialize driver: {str(e)}")