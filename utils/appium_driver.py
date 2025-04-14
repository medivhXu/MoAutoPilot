from appium import webdriver
import yaml
import os
from utils.app_inspector import AppInspector
from utils.environment_checker import EnvironmentChecker
from utils.logger import logger
import subprocess
import time
import urllib3
from selenium.common.exceptions import WebDriverException

class AppiumDriver:
    def __init__(self, platform='android emulator', check_env=True):
        self.platform = platform.lower()
        # 添加鸿蒙 OS 平台支持
        if self.platform not in ['ios', 'android', 'harmony', 'android emulator', 'ios emulator']:
            raise ValueError("Platform must be 'ios', 'android' or 'harmony'")
        
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
        
        logger.info(f"初始化 {platform.upper()} 测试环境...")
        
        # 加载配置
        try:
            self.config = self._load_config()
            logger.info("✓ 配置文件加载成功")
        except Exception as e:
            logger.error(f"✗ 配置文件加载失败: {str(e)}")
            raise
        
        # 设置 Appium 服务器地址
        self.appium_host = self.config.get('appium_server', {}).get('host') or os.getenv('APPIUM_HOST', 'localhost')
        self.appium_port = self.config.get('appium_server', {}).get('port') or os.getenv('APPIUM_PORT', '4723')
        logger.info(f"✓ Appium 服务器地址: {self.appium_host}:{self.appium_port}")

        # 获取可用的 Android 虚拟设备
        if self.platform == 'android emulator':
            avd_list = subprocess.run(['emulator', '-list-avds'], capture_output=True, text=True).stdout.strip().split('\n')
            if not avd_list:
                raise ValueError("未找到可用的 Android 虚拟设备。请确保已安装并配置了 Android Studio 的虚拟设备。")
            avd_name = avd_list[0]  # 使用第一个可用的 AVD
            logger.info(f"启动 Android 模拟器: {avd_name}")
            subprocess.Popen(['emulator', '-avd', avd_name, '-writable-system'])
            time.sleep(5)  # 等待模拟器启动

            # 检查设备是否已连接
            adb_devices = subprocess.run(['adb', 'devices'], capture_output=True, text=True).stdout
            if 'emulator' not in adb_devices:
                raise ValueError("Android 模拟器未连接。请确保模拟器已启动并可用。")
            logger.info("✓ Android 模拟器已连接")

    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"配置文件不存在: {config_path}") from e
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {str(e)}") from e

    def create_session(self):
        """创建 Appium 会话"""
        logger.info("创建 Appium 会话...")
        try:
            # 1. 检查 Appium 服务器状态
            if not self._check_server_running():
                error_msg = "\nAppium 服务器未运行，请检查:\n"
                error_msg += "1. Appium Desktop 是否已启动\n"
                error_msg += "2. 命令行 Appium 服务器是否已启动\n"
                error_msg += "3. 端口 4723 是否被占用\n"
                error_msg += "\n解决方案:\n"
                error_msg += "1. 启动 Appium Desktop\n"
                error_msg += "2. 或运行: appium --address localhost --port 4723\n"
                error_msg += "3. 检查端口占用: lsof -i :4723\n"
                raise ConnectionError(error_msg)

            # 2. 检查设备连接状态
            if self.platform == 'android emulator':
                adb_devices = subprocess.run(['adb', 'devices'], capture_output=True, text=True).stdout
                if 'emulator' not in adb_devices:
                    error_msg = "\nAndroid 模拟器未连接，请检查:\n"
                    error_msg += "1. 模拟器是否已启动\n"
                    error_msg += "2. adb 是否正常工作\n"
                    error_msg += "3. 模拟器是否响应\n"
                    error_msg += "\n解决方案:\n"
                    error_msg += "1. 启动模拟器: emulator -list-avds\n"
                    error_msg += "2. 检查 adb: adb devices\n"
                    error_msg += "3. 重启 adb: adb kill-server && adb start-server\n"
                    raise ConnectionError(error_msg)

            # 3. 检查 Appium 设置应用
            if not self._check_appium_settings():
                error_msg = "\n系统自带通讯录应用未正确安装，请检查:\n"
                error_msg += "1. 通讯录应用是否已安装\n"
                error_msg += "2. 应用权限是否正确\n"
                error_msg += "3. 应用版本是否兼容\n"
                error_msg += "\n解决方案:\n"
                error_msg += "1. 检查通讯录应用安装: adb shell pm list packages | grep com.android.chrome\n"
                raise RuntimeError(error_msg)

            # 4. 获取并验证设备配置
            caps = self._get_device_capabilities()
            server_url = f'http://{self.appium_host}:{self.appium_port}/wd/hub'
            logger.info(f"✓ 正在连接服务器: {server_url}")
            logger.info(f"✓ 使用配置参数: {caps}")
            
            # 5. 检查应用文件
            app_path = os.path.expanduser(caps.get('app', ''))
            if not os.path.exists(app_path):
                logger.warning(f"✗ 应用文件不存在: {app_path}")
                logger.warning("跳过应用文件检查，继续执行...")
            else:
                caps['app'] = app_path
                logger.info(f"✓ 应用文件路径: {app_path}")
            
            # 6. 初始化 WebDriver
            logger.info("正在初始化 WebDriver...")
            self.driver = webdriver.Remote(server_url, caps)
            logger.info("✓ WebDriver 初始化成功")
            
            # 7. 设置等待时间
            self.driver.implicitly_wait(self.config['test_info']['implicit_wait'])
            logger.info(f"✓ 设置隐式等待时间: {self.config['test_info']['implicit_wait']}秒")
            logger.info("✓ Appium 会话创建成功")
            return self.driver
            
        except urllib3.exceptions.MaxRetryError as e:
            error_msg = "\nAppium 连接失败，请检查:\n"
            error_msg += "1. Appium Desktop 是否已启动\n"
            error_msg += "2. Appium Desktop 是否正在监听端口 4723\n"
            error_msg += "3. 网络连接是否正常\n"
            error_msg += "4. 防火墙设置是否允许连接\n"
            error_msg += "\n解决方案:\n"
            error_msg += "1. 重启 Appium Desktop\n"
            error_msg += "2. 检查端口: lsof -i :4723\n"
            error_msg += "3. 测试连接: curl http://localhost:4723/status\n"
            error_msg += f"\n详细错误: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        except KeyError as e:
            error_msg = f"✗ 配置文件缺少必要的配置项: {str(e)}"
            error_msg += "\n\n解决方案:\n"
            error_msg += "1. 检查 config.yaml 文件格式\n"
            error_msg += "2. 确保所有必要的配置项都已设置\n"
            error_msg += "3. 参考示例配置文件\n"
            logger.error(error_msg)
            logger.error(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
            raise KeyError(error_msg) from e
        except WebDriverException as e:
            error_msg = f"✗ 连接 Appium 服务器失败: {str(e)}"
            error_msg += "\n\n可能的原因:\n"
            error_msg += "1. 设备未连接或未响应\n"
            error_msg += "2. 应用未安装或版本不匹配\n"
            error_msg += "3. 权限问题\n"
            error_msg += "\n解决方案:\n"
            error_msg += "1. 检查设备连接: adb devices\n"
            error_msg += "2. 检查应用安装: adb shell pm list packages\n"
            error_msg += "3. 检查应用权限: adb shell pm list permissions\n"
            logger.error(error_msg)
            logger.error(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
            raise ConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"✗ 创建 Appium 会话失败: {str(e)}"
            error_msg += "\n\n调试信息:\n"
            error_msg += f"错误类型: {type(e)}\n"
            error_msg += f"错误详情: {e.__class__.__name__}: {str(e)}\n"
            if hasattr(e, '__traceback__'):
                import traceback
                error_msg += f"\n错误堆栈:\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _check_appium_settings(self):
        """检查系统自带通讯录应用是否可用"""
        try:
            # 检查通讯录应用是否已安装
            result = subprocess.run(
                ['adb', '-s', 'emulator-5554', 'shell', 'pm', 'list', 'packages', 'com.android.chrome'],
                capture_output=True,
                text=True
            )
            if 'com.android.chrome' not in result.stdout:
                logger.error("系统自带通讯录应用未安装或不可用")
                return False

            logger.info("✓ 系统自带通讯录应用已正确安装")
            return True
        except Exception as e:
            logger.error(f"检查通讯录应用失败: {str(e)}")
            return False

    def _get_device_capabilities(self):
        """获取设备配置"""
        try:
            # 获取平台特定的配置
            device_configs = self.config.get('devices', {}).get(self.platform, [])
            if not device_configs:
                raise ValueError(f"未找到 {self.platform} 平台的设备配置")

            # 获取指定设备或默认设备的配置
            device_name = os.getenv('DEVICE_NAME')
            if device_name:
                # 如果指定了设备名称，查找匹配的设备
                device = next(
                    (d for d in device_configs if d.get('deviceName') == device_name),
                    None
                )
                if not device:
                    raise ValueError(f"未找到指定的设备配置: {device_name}")
            else:
                # 使用默认设备（第一个设备）
                default_index = self.config.get('test_info', {}).get('default_device', 0)
                if default_index >= len(device_configs):
                    raise ValueError(f"默认设备索引 {default_index} 超出范围")
                device = device_configs[default_index]

            logger.info(f"✓ 使用设备配置: {device.get('name', device.get('deviceName'))}")
            
            # 基础配置
            caps = {
                'platformName': self.platform.capitalize(),
                'automationName': 'XCUITest' if self.platform == 'ios' else 'UiAutomator2',
                'noReset': True,
                'skipServerInstallation': True,  # 跳过服务器安装
                'skipDeviceInitialization': True,  # 跳过设备初始化
                'enforceAppInstall': False,  # 不强制安装应用
                'autoGrantPermissions': True,  # 自动授予权限
                'newCommandTimeout': 60,  # 新命令超时时间
                'autoLaunch': False  # 不自动启动应用
            }

            # 合并设备特定配置
            caps.update(device)

            # 检查必要的配置项
            required_caps = ['deviceName', 'platformVersion']
            missing_caps = [cap for cap in required_caps if not caps.get(cap)]
            if missing_caps:
                raise KeyError(f"缺少必要的配置项: {', '.join(missing_caps)}")

            return caps

        except (KeyError, IndexError) as e:
            raise KeyError(f"设备配置格式错误: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"获取设备配置失败: {str(e)}") from e

    def start_server(self) -> bool:
        """启动 Appium 服务器"""
        try:
            # 检查 Node.js 版本和 Appium 环境
            checker = EnvironmentChecker()
            if not checker.check_node_and_appium():
                logger.error("环境检查失败，请确保 Node.js 和 Appium 环境正常。")
                return False

            # 首先检查 Appium Desktop 是否正在运行
            if self._check_appium_desktop():
                logger.info("检测到 Appium Desktop 正在运行")
                # 检查服务器是否可访问
                if self._check_server_running():
                    logger.info("✓ Appium Desktop 服务器运行正常")
                    return True
                else:
                    logger.error("Appium Desktop 服务器未响应，请检查服务器状态")
                    return False

            # 检查端口是否被占用
            if self._is_port_in_use(self.appium_port):
                logger.warning(f"端口 {self.appium_port} 已被占用，但未检测到 Appium Desktop")
                logger.warning("请检查是否有其他程序占用了该端口")
                return False

            # 如果没有检测到 Appium Desktop 运行，尝试启动命令行服务器
            logger.info(f"正在启动命令行 Appium 服务器 (host: {self.appium_host}, port: {self.appium_port})...")
            
            # 使用 localhost 而不是 0.0.0.0
            self.server_process = subprocess.Popen(
                ['appium', '--address', 'localhost', '--port', str(self.appium_port), '--relaxed-security'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服务器启动
            time.sleep(5)
            
            # 检查服务器是否成功启动
            if not self._check_server_running():
                logger.error("✗ Appium 服务器启动失败")
                if self.server_process:
                    self.server_process.terminate()
                return False
                
            logger.info("✓ Appium 服务器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"✗ 启动 Appium 服务器失败: {str(e)}")
            if self.server_process:
                self.server_process.terminate()
            return False

    def _check_appium_desktop(self):
        """检查 Appium Desktop 是否已启动"""
        import platform
        import subprocess
        
        system = platform.system().lower()
        try:
            if system == 'darwin':  # macOS
                # 检查 Appium Desktop 进程
                result = subprocess.run(['ps', '-A'], capture_output=True, text=True)
                # 检查可能的进程名
                process_names = ['Appium Desktop', 'Appium', 'appium-desktop']
                return any(name in result.stdout for name in process_names)
            elif system == 'windows':
                # 检查 Appium Desktop 进程
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                # 检查可能的进程名
                process_names = ['Appium Desktop', 'Appium', 'appium-desktop']
                return any(name in result.stdout for name in process_names)
            else:  # Linux
                # 检查 Appium Desktop 进程
                result = subprocess.run(['ps', '-A'], capture_output=True, text=True)
                # 检查可能的进程名
                process_names = ['Appium Desktop', 'Appium', 'appium-desktop']
                return any(name in result.stdout for name in process_names)
        except Exception as e:
            logger.warning(f"检查 Appium Desktop 状态失败: {str(e)}")
            # 如果进程检查失败，尝试直接检查服务器是否可访问
            return self._check_server_running()

    def _check_server_running(self):
        """检查 Appium 服务器是否正在运行"""
        import http.client
        try:
            conn = http.client.HTTPConnection(self.appium_host, int(self.appium_port), timeout=1)
            
            # 尝试 Appium 2.0 的路径
            conn.request("GET", "/wd/hub/status")
            response = conn.getresponse()
            response.read()  # 清空响应缓冲区
            
            if response.status == 404:
                # 如果 2.0 路径失败，尝试 1.x 的路径
                conn = http.client.HTTPConnection(self.appium_host, int(self.appium_port), timeout=1)
                conn.request("GET", "/status")
                response = conn.getresponse()
            
            return response.status in [200, 404]  # 404 也表示服务器在运行，只是路径不对
            
        except Exception as e:
            logger.error(f'✗ 检查服务器状态失败：{e}')
            return False
        finally:
            try:
                conn.close()
            except:
                pass

    def _is_port_in_use(self, port):
        """检查端口是否被占用"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 尝试绑定端口
            sock.bind(('localhost', int(port)))
            sock.close()
            return False
        except socket.error:
            sock.close()
            return True

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