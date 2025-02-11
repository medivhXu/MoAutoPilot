import subprocess
import platform
import os
from typing import Dict
from utils.progress_bar import ProgressBar
import sys
import pytest
import json
import re
import time
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
        
        # 检查 Android 环境
        print("\n3. 检查 Android 环境...", file=sys.stderr)
        self.check_android_environment()
        progress.print_progress(3)
        
        # 检查 iOS 环境
        print("\n4. 检查 iOS 环境...", file=sys.stderr)
        self.check_ios_environment()
        progress.print_progress(4)
        
        # 检查 Appium 环境
        print("\n5. 检查 Appium 环境...", file=sys.stderr)
        self.check_appium_environment()
        progress.print_progress(5)

        if not self.results['status']:
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
            pytest.skip(error_msg)

        return self.results

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

    def check_java_environment(self):
        """检查 Java 环境"""
        try:
            result = self._run_with_retry(['java', '-version'])
            
            if result.returncode == 0:
                version = result.stderr.split('\n')[0]
                version_match = re.search(r'version "(.*?)"', version)
                if version_match:
                    version_str = version_match.group(1)
                    if version_str.startswith('1.8') or version_str.startswith('8.'):
                        self.results['details']['java'] = {'version': version}
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
                print(f"✓ Appium 版本: {result.stdout.strip()}", file=sys.stderr)
                
                # 检查 Appium 驱动
                result = self._run_with_retry(['appium', 'driver', 'list', '--json'])
                
                try:
                    drivers_json = json.loads(result.stdout)
                    for driver in drivers_json:
                        if driver['name'] == '@appium/uiautomator2-driver':
                            version = driver['version']
                            if not version.startswith('2.'):
                                self.results['status'] = False
                                self.results['missing'].append(f'appium-uiautomator2-driver v2.x (当前: {version})')
                            else:
                                print("✓ UIAutomator2 驱动已安装", file=sys.stderr)
                        elif driver['name'] == '@appium/xcuitest-driver':
                            version = driver['version']
                            if not version.startswith('4.'):
                                self.results['status'] = False
                                self.results['missing'].append(f'appium-xcuitest-driver v4.x (当前: {version})')
                            else:
                                print("✓ XCUITest 驱动已安装", file=sys.stderr)
                except json.JSONDecodeError:
                    # 降级为简单字符串检查
                    drivers_output = result.stdout.lower()
                    if '@appium/uiautomator2-driver' not in drivers_output:
                        self.results['status'] = False
                        self.results['missing'].append('appium-uiautomator2-driver')
                    if '@appium/xcuitest-driver' not in drivers_output:
                        self.results['status'] = False
                        self.results['missing'].append('appium-xcuitest-driver')
            else:
                self.results['status'] = False
                self.results['missing'].append('Appium')
            
        except Exception as e:
            self.results['status'] = False
            self.results['details']['appium'] = {'error': str(e)}

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
                                print(f"✓ Emulator 可用", file=sys.stderr)
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

            # 4. 检查 platform 版本
            platforms_path = os.path.join(android_home, 'platforms')
            if os.path.exists(platforms_path):
                versions = os.listdir(platforms_path)
                if not versions:
                    self.results['status'] = False
                    self.results['missing'].append('Android platforms')
                else:
                    latest_platform = sorted(versions)[-1]
                    print(f"✓ Android Platform: {latest_platform}", file=sys.stderr)
            else:
                self.results['status'] = False
                self.results['missing'].append('Android platforms')

            # 保存检查结果
            self.results['details']['android'] = {
                'sdk_path': android_home,
                'build_tools': latest_version if 'latest_version' in locals() else None,
                'platform': latest_platform if 'latest_platform' in locals() else None
            }

        except Exception as e:
            self.results['status'] = False
            self.results['details']['android'] = {'error': str(e)}
            self._add_solution('Android SDK')

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