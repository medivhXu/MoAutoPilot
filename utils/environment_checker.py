import platform
import os
from typing import Dict
from utils.progress_bar import ProgressBar
import sys
import subprocess
import time
import pytest
import json
import re
import concurrent.futures
from datetime import datetime, timedelta
import pickle

class EnvironmentCache:
    def __init__(self, cache_file='.env_cache', ttl=timedelta(hours=1)):
        self.cache_file = cache_file
        self.ttl = ttl

    def get(self):
        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
                if datetime.now() - data['timestamp'] < self.ttl:
                    return data['results']
        except:
            pass
        return None

    def set(self, results):
        with open(self.cache_file, 'wb') as f:
            pickle.dump({
                'timestamp': datetime.now(),
                'results': results
            }, f)

class EnvironmentChecker:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.colors = {
            'HEADER': '\033[95m',    # 紫色
            'BLUE': '\033[94m',      # 蓝色
            'GREEN': '\033[92m',     # 绿色
            'YELLOW': '\033[93m',    # 黄色
            'RED': '\033[91m',       # 红色
            'BOLD': '\033[1m',       # 加粗
            'UNDERLINE': '\033[4m',  # 下划线
            'END': '\033[0m'         # 结束颜色
        }
        self.results = {
            'status': True,
            'details': {},
            'missing': [],
            'recommendations': [],
            'solutions': {}  # 新增解决方案字典
        }

        # 定义各组件的解决方案
        self.solution_map = {
            'Java JDK': {
                'darwin': {
                    'command': 'brew tap adoptopenjdk/openjdk && brew install adoptopenjdk8',
                    'manual': 'https://adoptium.net/temurin/releases/?version=8',
                    'env_setup': '''
# 添加到 ~/.bash_profile 或 ~/.zshrc:
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)
export PATH=$JAVA_HOME/bin:$PATH'''
                },
                'linux': {
                    'command': 'sudo apt-get install openjdk-8-jdk',
                    'manual': 'https://adoptium.net/temurin/releases/?version=8',
                    'env_setup': '''
# 添加到 ~/.bashrc:
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH'''
                },
                'windows': {
                    'manual': 'https://adoptium.net/temurin/releases/?version=8',
                    'env_setup': '''
# 设置环境变量:
1. 右键"此电脑" -> 属性 -> 高级系统设置 -> 环境变量
2. 新建系统变量 JAVA_HOME，值为 JDK 安装路径
3. 编辑 Path 变量，添加 %JAVA_HOME%\\bin'''
                }
            },
            'Android SDK': {
                'darwin': {
                    'command': 'brew install android-commandlinetools',
                    'manual': 'https://developer.android.com/studio#downloads'
                },
                'linux': {
                    'manual': 'https://developer.android.com/studio#downloads'
                },
                'windows': {
                    'manual': 'https://developer.android.com/studio#downloads'
                }
            },
            'Node.js': {
                'darwin': {
                    'command': 'brew install node',
                    'manual': 'https://nodejs.org/en/download/'
                },
                'linux': {
                    'command': 'sudo apt-get install nodejs npm',
                    'manual': 'https://nodejs.org/en/download/'
                },
                'windows': {
                    'manual': 'https://nodejs.org/en/download/'
                }
            },
            'Appium': {
                'all': {
                    'command': 'npm install -g appium',
                    'drivers': {
                        'android': 'appium driver install uiautomator2',
                        'ios': 'appium driver install xcuitest'
                    }
                }
            },
            'WebDriverAgent': {
                'darwin': {
                    'command': 'xcode-select --install && brew install carthage',
                    'manual': 'https://github.com/appium/WebDriverAgent#installation'
                }
            }
        }

    def _add_solution(self, component):
        """添加组件的解决方案"""
        if component in self.solution_map:
            solution = self.solution_map[component]
            if 'all' in solution:
                solution = solution['all']
            elif self.os_type in solution:
                solution = solution[self.os_type]
            else:
                return

            self.results['solutions'][component] = solution

    def check_all(self, auto_install=True) -> Dict:
        """检查所有环境依赖"""
        print("\n开始检查环境配置...", file=sys.stderr)
        progress = ProgressBar(5, prefix='环境检查:', suffix='完成')

        # 检查 Python 环境
        print("\n1. 检查 Python 环境...", file=sys.stderr)
        self.check_python_environment()
        progress.print_progress(1)

        # 检查 Java 环境
        print("\n2. 检查 Java 环境...", file=sys.stderr)
        self.check_java_environment()
        progress.print_progress(2)

        # 检查 Appium 环境
        print("\n3. 检查 Appium 环境...", file=sys.stderr)
        self.check_appium_environment()
        progress.print_progress(3)

        # 检查 Android 环境
        print("\n4. 检查 Android 环境...", file=sys.stderr)
        self.check_android_environment()
        progress.print_progress(4)

        # # 检查 iOS 环境
        # print("\n5. 检查 iOS 环境...", file=sys.stderr)
        # self.check_ios_environment()
        # progress.print_progress(5)

        if not self.results['status']:
            self._print_error_message()
            pytest.skip("环境检查失败")

        return self.results

    def _print_error_message(self):
        """打印错误信息"""
        error_msg = "\n环境检查失败，请按以下步骤配置环境:\n"

        # 检查并显示环境变量问题
        if 'ANDROID_HOME' not in os.environ and 'ANDROID_SDK_ROOT' not in os.environ:
            error_msg += f"\n{self.colors['RED']}缺少 Android SDK 环境变量:{self.colors['END']}"
            error_msg += "\n请在 ~/.zshrc 或 ~/.bash_profile 中添加:"
            error_msg += "\nexport ANDROID_HOME=$HOME/Library/Android/sdk"
            error_msg += "\nexport PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools\n"

        # 检查并显示 Node.js 版本问题
        if 'Node.js v18' in self.results['missing']:
            error_msg += f"\n{self.colors['RED']}Node.js 版本不符合要求:{self.colors['END']}"
            error_msg += f"\n当前版本: {self.results.get('details', {}).get('node_version', '未安装')}"
            error_msg += "\n需要版本: v18.x.x\n"

        # 检查并显示 Appium 驱动问题
        if any(driver in self.results['missing'] for driver in ['appium-uiautomator2-driver', 'appium-xcuitest-driver']):
            error_msg += f"\n{self.colors['RED']}缺少 Appium 驱动:{self.colors['END']}"
            error_msg += "\n请执行以下命令安装驱动:"
            if 'appium-uiautomator2-driver' in self.results['missing']:
                error_msg += "\nappium driver install uiautomator2"
            if 'appium-xcuitest-driver' in self.results['missing']:
                error_msg += "\nappium driver install xcuitest\n"

        # 检查并显示 Android 工具问题
        android_tools = [tool for tool in self.results['missing'] if tool.startswith('Android')]
        if android_tools:
            error_msg += f"\n{self.colors['RED']}缺少 Android 开发工具:{self.colors['END']}"
            for tool in android_tools:
                error_msg += f"\n- {tool}"
            error_msg += "\n\n推荐使用 Android Studio 安装这些组件:"
            error_msg += "\n1. 打开 Android Studio"
            error_msg += "\n2. 转到 Tools -> SDK Manager"
            error_msg += "\n3. 在 SDK Tools 标签页中安装:"
            error_msg += "\n   - Android SDK Build-tools"
            error_msg += "\n   - Android SDK Platform-tools"
            error_msg += "\n   - Android Emulator\n"

        error_msg += f"\n{self.colors['YELLOW']}注意:{self.colors['END']} 请按顺序解决以上问题:"
        error_msg += "\n1. 首先配置环境变量"
        error_msg += "\n2. 然后安装/升级 Node.js"
        error_msg += "\n3. 接着安装 Appium 及其驱动"
        error_msg += "\n4. 最后配置 Android 开发环境"
        error_msg += f"\n\n{self.colors['GREEN']}完成上述配置后，重新运行测试{self.colors['END']}"

        print(error_msg, file=sys.stderr)

    def check_all_parallel(self, auto_install=True) -> Dict:
        """并行检查所有环境依赖"""
        # 尝试从缓存获取结果
        cache = EnvironmentCache()
        cached_results = cache.get()
        if cached_results:
            return cached_results

        print("\n开始并行检查环境配置...", file=sys.stderr)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.check_python_environment): "Python",
                executor.submit(self.check_java_environment): "Java",
                executor.submit(self.check_android_environment): "Android",
                executor.submit(self.check_ios_environment): "iOS",
                executor.submit(self.check_appium_environment): "Appium"
            }

            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    future.result()
                    print(f"✓ {name} 环境检查完成", file=sys.stderr)
                except Exception as e:
                    print(f"✗ {name} 环境检查失败: {str(e)}", file=sys.stderr)

        # 缓存结果
        cache.set(self.results)
        return self.results

    def check_python_environment(self):
        """检查 Python 环境"""
        try:
            import importlib.metadata as importlib_metadata
            required = {
                'Appium-Python-Client': '2.11.1',
                'selenium': '4.15.2',
                'pytest': '7.4.3'
            }

            installed = {dist.metadata['Name']: dist.version
                        for dist in importlib_metadata.distributions()}

            missing = []
            for package, version in required.items():
                if package.lower() not in {k.lower(): v for k, v in installed.items()}:
                    missing.append(f"{package}>={version}")

            self.results['details']['python'] = {
                'version': platform.python_version(),
                'packages': installed,
                'missing': missing
            }

            if missing:
                self.results['status'] = False
                self.results['missing'].extend(missing)
                self.results['recommendations'].append(
                    f"运行: pip install {' '.join(missing)}"
                )
        except Exception as e:
            self.results['status'] = False
            self.results['details']['python'] = {'error': str(e)}
        # finally:
        #     print(f"python环境检查结果：{self.results}")

    def check_java_environment(self):
        """检查 Java 环境"""
        try:
            result = self._run_with_retry(['java', '-version'])
            if result.returncode == 0:
                # Java -version 输出到 stderr，且已经是字符串格式
                version_output = result.stderr.split('\n')[0]
                version_match = re.search(r'version "([^"]+)"', version_output)
                if version_match:
                    version_str = version_match.group(1)
                    if version_str.startswith('1.8') or version_str.startswith('8.'):
                        self.results['details']['java'] = {'version': version_str}
                        print(f"✓ Java 版本: {version_str}", file=sys.stderr)
                        return  # Java 8 检查通过，直接返回
                    else:
                        self.results['status'] = False
                        self.results['missing'].append(f'Java JDK 8 (当前: {version_str})')
                        self._add_solution('Java JDK')
                else:
                    self.results['status'] = False
                    self.results['missing'].append('Java JDK 8')
                    self._add_solution('Java JDK')
            else:
                self.results['status'] = False
                self.results['missing'].append('Java JDK 8')
                self._add_solution('Java JDK')
        except Exception as e:
            self.results['status'] = False
            self.results['missing'].append('Java JDK 8')
            self._add_solution('Java JDK')
            self.results['details']['java'] = {'error': str(e)}
        # finally:
        #     print(f"java环境检查结果：{self.results}")

    def check_appium_environment(self):
        """检查 Appium 环境"""
        try:
            # 检查 Node.js
            result = self._run_with_retry(['node', '-v'])
            node_version = result.stdout.strip()
            version_num = node_version.lstrip('v').split('.')
            if not (version_num[0] == '18' or version_num[0] == '20'):
                self.results['status'] = False
                self.results['missing'].append('Node.js v18/v20')
                self.results['details']['node'] = {'version': node_version}
            else:
                print(f"✓ Node.js 版本: {node_version}", file=sys.stderr)

            # 检查 Appium
            result = self._run_with_retry(['appium', '-v'])
            if result.returncode == 0:
                appium_version = result.stdout.strip()
                print(f"✓ Appium 版本: {appium_version}", file=sys.stderr)
                self.results['details']['appium'] = {'version': appium_version}

                # 检查 Appium 驱动
                result = self._run_with_retry(['appium', 'driver', 'list', '--installed'])
                drivers_output = result.stdout or result.stderr
                print(f"驱动列表输出: {drivers_output}", file=sys.stderr)

                # 检查 uiautomator2 驱动
                if 'uiautomator2' in drivers_output:
                    if 'appium' not in self.results['details']:
                        self.results['status'] = True
                else:
                    self.results['status'] = False
                    self.results['missing'].append('appium-uiautomator2-driver')
                
                # 检查 xcuitest 驱动
                if 'xcuitest' in drivers_output:
                    self.results['status'] = True
                else:
                    self.results['status'] = False
                    self.results['missing'].append('appium-xcuites-driver')
                
                    
        except json.JSONDecodeError:
            # 如果 JSON 解析失败，尝试使用 list 命令检查
            print("使用备选方法检查驱动...", file=sys.stderr)
            result = self._run_with_retry(['appium', 'driver', 'list', '--installed'])
            drivers_output = result.stdout.lower()
            
            # 直接检查输出文本中是否包含驱动名称
            if '@appium/uiautomator2-driver' in drivers_output:
                print("✓ UIAutomator2 驱动已安装", file=sys.stderr)
                # 获取版本信息（如果需要）
                version_result = self._run_with_retry(['appium', 'driver', 'list', '--installed', '--json'])
                try:
                    drivers_json = json.loads(version_result.stdout)
                    for driver in drivers_json:
                        if driver.get('name') == '@appium/uiautomator2-driver':
                            print(f"  版本: {driver.get('version', 'unknown')}", file=sys.stderr)
                            self.results['details']['appium']['uiautomator2'] = driver.get('version')
                except:
                    pass
            else:
                self.results['status'] = False
                self.results['missing'].append('appium-uiautomator2-driver')
                self._add_solution('Appium')
            
            if '@appium/xcuitest-driver' in drivers_output:
                print("✓ XCUITest 驱动已安装", file=sys.stderr)
                # 获取版本信息（如果需要）
                version_result = self._run_with_retry(['appium', 'driver', 'list', '--installed', '--json'])
                try:
                    drivers_json = json.loads(version_result.stdout)
                    for driver in drivers_json:
                        if driver.get('name') == '@appium/xcuitest-driver':
                            print(f"  版本: {driver.get('version', 'unknown')}", file=sys.stderr)
                            self.results['details']['appium']['xcuitest'] = driver.get('version')
                except:
                    pass
            else:
                self.results['status'] = False
                self.results['missing'].append('appium-xcuitest-driver')
                self._add_solution('Appium')

        except Exception as e:
            self.results['status'] = False
            self.results['details']['appium'] = {'error': str(e)}
            print(f"Appium 环境检查失败: {str(e)}", file=sys.stderr)



    def check_android_environment(self):
        """检查 Android 环境"""
        try:
            # 1. 查找 Android SDK 路径
            android_home = self._find_android_sdk()
            if not android_home:
                self.results['status'] = False
                self.results['missing'].append('Android SDK')
                self._add_solution('Android SDK')
                return

            # 2. 检查必要的工具和目录
            required_tools = {
                'platform-tools': ['adb'],
                'emulator': ['emulator'],
                'build-tools': ['aapt', 'aapt2', 'zipalign']
            }

            for folder, tools in required_tools.items():
                folder_path = os.path.join(android_home, folder)
                if not os.path.exists(folder_path):
                    self.results['status'] = False
                    self.results['missing'].append(f'Android {folder}')
                    continue

                # 在 PATH 中检查工具
                for tool in tools:
                    # print(f"android工具版本检测:{tool}") 
                    try:
                        if folder == 'platform-tools':
                            result = self._run_with_retry(['adb', 'version'])
                            if result.returncode == 0:
                                print(f"✓ ADB 可用: {result.stdout.strip()}", file=sys.stderr)
                            else:
                                self.results['status'] = False
                                self.results['missing'].append('Android platform-tools')
                        elif folder == 'emulator':
                            result = self._run_with_retry(['emulator', '-version'])
                            if result.returncode == 0:
                                print("✓ Emulator 可用", file=sys.stderr)
                            else:
                                self.results['status'] = False
                                self.results['missing'].append('Android emulator')
                    except FileNotFoundError:
                        self.results['status'] = False
                        self.results['missing'].append(f'Android {folder}')

            # 3. 检查 build-tools 版本
            build_tools_path = os.path.join(android_home, 'build-tools')
            if os.path.exists(build_tools_path):
                versions = os.listdir(build_tools_path)
                if not versions:
                    self.results['status'] = False
                    self.results['missing'].append('Android build-tools')
                else:
                    latest_version = sorted(versions)[-1]
                    print(f"✓ Build Tools 版本: {latest_version}", file=sys.stderr)
            else:
                self.results['status'] = False
                self.results['missing'].append('Android build-tools')


            # 保存检查结果
            self.results['details']['android'] = {
                'sdk_path': android_home,
                'build_tools': latest_version if 'latest_version' in locals() else None,
            }

        except Exception as e:
            self.results['status'] = False
            self.results['details']['android'] = {'error': str(e)}
            self._add_solution('Android SDK')
        # finally:
        #     print(f"android环境检查结果：{self.results}")

    def _find_android_sdk(self):
        """
        查找Android SDK的路径。
        
        Returns:
            str: Android SDK的路径，如果未找到，则返回None。
        """
        
        # 如果没有找到Android SDK，尝试查找ANDROID_HOME环境变量
        andorid_home = os.environ.get('ANDROID_HOME')
        if andorid_home:
            android_platform_tools_path = os.path.join(andorid_home, 'platform-tools')
            android_build_tools_path = os.path.join(andorid_home, 'build-tools')
            if os.path.exists(android_platform_tools_path) and os.path.exists(android_build_tools_path):
                return andorid_home
    
        # 如果没有找到Android SDK，返回None
            return None

    def _get_paths(self):
        """
        获取可能的Android SDK路径列表。
        
        Returns:
            list: 可能的Android SDK路径列表。
        """
        paths = []
        # home_dir = os.path.expanduser('~')
        for dir in ['~/Library/Android/sdk']:
            paths.append(dir)
        
        # 可以在此处添加更多可能的路径
        return paths
    
    def _run_with_retry(self, cmd):
        """在异常时重试命令的执行"""
        max_retries = 3
        delay = 1
        retries = 0
        
        while retries < max_retries:
            try:
                result = subprocess.run(cmd, 
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     encoding='utf-8')
                # 合并 stdout 和 stderr 的输出
                output = result.stdout or result.stderr
                # 创建一个新的类似 CompletedProcess 的对象，但包含合并的输出
                return type('CommandResult', (), {
                    'returncode': result.returncode,
                    'stdout': output,
                    'stderr': output,
                    'original': result
                })
            except Exception as e:
                print(f"Error: {str(e)}")
                if retries == max_retries - 1:
                    raise
                time.sleep(delay)
                retries += 1
        
        raise Exception("All retries failed")

    def print_report(self):
        """打印环境检查报告"""
        print("\n=== 环境检查报告 ===")
        print(f"\n状态: {'✓ 通过' if self.results['status'] else '✗ 失败'}")

        if not self.results['status']:
            print("\n缺失组件:")
            for item in self.results['missing']:
                print(f"  - {item}")

            print("\n建议操作:")
            for rec in self.results['recommendations']:
                print(f"  - {rec}")

        print("\n详细信息:")
        for category, details in self.results['details'].items():
            print(f"\n{category.upper()}:")
            for key, value in details.items():
                print(f"  {key}: {value}")

    def check_ios_environment(self):
        """检查 iOS 环境"""
        try:
            # 1. 检查 Xcode 是否安装
            result = self._run_with_retry(['xcodebuild', '-version'])
            if result.returncode == 0:
                xcode_version = result.stdout.split('\n')[0].split(' ')[-1]
                print(f"✓ Xcode 版本: {xcode_version}", file=sys.stderr)
                self.results['details']['ios'] = {'xcode_version': xcode_version}
                
                if float(xcode_version.split('.')[0]) < 12:
                    self.results['status'] = False
                    self.results['missing'].append(f'Xcode 12+ (当前: {xcode_version})')
                    self.results['recommendations'].append("请从 App Store 更新 Xcode 到最新版本")
            else:
                self.results['status'] = False
                self.results['missing'].append('Xcode')
                self.results['recommendations'].append("请从 App Store 安装 Xcode")
                return

            # 2. 检查 iOS SDK
            result = self._run_with_retry(['xcrun', '--sdk', 'iphoneos', '--show-sdk-version'])
            if result.returncode == 0:
                sdk_version = result.stdout.strip()
                print(f"✓ iOS SDK 版本: {sdk_version}", file=sys.stderr)
                self.results['details']['ios']['sdk_version'] = sdk_version
                
                if float(sdk_version.split('.')[0]) < 13:
                    self.results['status'] = False
                    self.results['missing'].append(f'iOS SDK 13+ (当前: {sdk_version})')
                    self.results['recommendations'].append(
                        "请在 Xcode -> Preferences -> Components 中下载更新的 iOS SDK"
                    )
            else:
                self.results['status'] = False
                self.results['missing'].append('iOS SDK')
                self.results['recommendations'].append(
                    "请运行: xcode-select --install 安装命令行工具"
                )

            # 3. 检查 WebDriverAgent
            wda_path = os.path.expanduser('~/.appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent')
            if not os.path.exists(wda_path):
                self.results['status'] = False
                self.results['missing'].append('WebDriverAgent')
                self.results['recommendations'].extend([
                    "请按顺序执行以下步骤安装 WebDriverAgent:",
                    "1. npm uninstall -g appium",
                    "2. npm install -g appium",
                    "3. appium driver install xcuitest",
                    "4. cd ~/.appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent",
                    "5. xcodebuild -project WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination 'id=<设备 UDID>' test"
                ])

            # 4. 检查开发者证书
            result = self._run_with_retry(['security', 'find-identity', '-v', '-p', 'codesigning'])
            if result.returncode == 0:
                if 'iPhone Developer' in result.stdout:
                    print("✓ 开发者证书已配置", file=sys.stderr)
                    self.results['details']['ios']['certificates'] = True
                else:
                    self.results['status'] = False
                    self.results['missing'].append('iOS Developer Certificate')
                    self.results['recommendations'].extend([
                        "请按顺序执行以下步骤配置开发者证书:",
                        "1. 打开 Xcode -> Preferences -> Accounts",
                        "2. 添加 Apple ID 并登录",
                        "3. 选择团队并点击 Manage Certificates",
                        "4. 点击 + 号添加 iOS Development Certificate"
                    ])
            else:
                self.results['status'] = False
                self.results['missing'].append('iOS Developer Certificate')
                self.results['recommendations'].append("请检查 Keychain Access 是否正常")

            # 5. 检查环境变量
            required_vars = ['DEVELOPER_DIR', 'DEVELOPMENT_TEAM', 'BUNDLE_IDENTIFIER']
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                self.results['status'] = False
                self.results['missing'].extend([f'环境变量: {var}' for var in missing_vars])
                env_setup_guide = {
                    'DEVELOPER_DIR': 'export DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"',
                    'DEVELOPMENT_TEAM': 'export DEVELOPMENT_TEAM="你的开发者团队 ID"  # 在 Xcode -> Preferences -> Accounts 中查看',
                    'BUNDLE_IDENTIFIER': 'export BUNDLE_IDENTIFIER="com.your.app"  # 替换为你的应用 Bundle ID'
                }
                self.results['recommendations'].append(
                    "请在 ~/.zshrc 或 ~/.bash_profile 中添加以下环境变量:\n" +
                    "\n".join([env_setup_guide[var] for var in missing_vars])
                )

        except Exception as e:
            self.results['status'] = False
            self.results['details']['ios'] = {'error': str(e)}
            print(f"iOS 环境检查失败: {str(e)}", file=sys.stderr)
            self.results['recommendations'].append(
                f"遇到未知错误: {str(e)}\n请确保 Xcode 和命令行工具正确安装"
            )

