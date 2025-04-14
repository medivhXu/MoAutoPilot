import subprocess
import platform
import os
import sys
from utils.progress_bar import ProgressBar
from utils.logger import logger

class EnvironmentInstaller:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.is_admin = self._check_admin()
        
        # 配置镜像源
        self.mirrors = {
            'pip': {
                'default': 'https://pypi.org/simple',
                'mirrors': [
                    'https://mirrors.aliyun.com/pypi/simple/',
                    'https://pypi.tuna.tsinghua.edu.cn/simple',
                    'https://mirrors.cloud.tencent.com/pypi/simple'
                ]
            },
            'npm': {
                'default': 'https://registry.npmjs.org/',
                'mirrors': [
                    'https://registry.npmmirror.com',
                    'https://mirrors.cloud.tencent.com/npm/',
                    'https://mirrors.huaweicloud.com/repository/npm/'
                ]
            },
            'brew': {
                'default': 'https://github.com',
                'mirrors': [
                    'https://mirrors.aliyun.com/homebrew',
                    'https://mirrors.tuna.tsinghua.edu.cn/git/homebrew',
                    'https://mirrors.ustc.edu.cn/brew.git'
                ]
            }
        }
        
        self.current_mirrors = {
            'pip': self.mirrors['pip']['default'],
            'npm': self.mirrors['npm']['default'],
            'brew': self.mirrors['brew']['default']
        }

    def _check_admin(self):
        """检查是否有管理员权限"""
        try:
            if self.os_type == 'windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False

    def _switch_mirror(self, package_manager, timeout=10):
        """切换到下一个可用的镜像源"""
        current = self.current_mirrors[package_manager]
        mirrors = self.mirrors[package_manager]['mirrors']
        
        # 测试镜像源连接性
        for mirror in mirrors:
            try:
                if package_manager == 'pip':
                    subprocess.run([sys.executable, '-m', 'pip', 'config', 'set', 'global.index-url', mirror],
                                 check=True, timeout=timeout)
                elif package_manager == 'npm':
                    subprocess.run(['npm', 'config', 'set', 'registry', mirror],
                                 check=True, timeout=timeout)
                elif package_manager == 'brew' and self.os_type == 'darwin':
                    # 设置 Homebrew 镜像
                    os.environ['HOMEBREW_BREW_GIT_REMOTE'] = mirror
                    os.environ['HOMEBREW_CORE_GIT_REMOTE'] = f"{mirror}/homebrew-core"
                
                logger.info(f"已切换到{package_manager}镜像源: {mirror}")
                self.current_mirrors[package_manager] = mirror
                return True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue
        
        logger.warning(f"所有{package_manager}镜像源均不可用，使用默认源")
        return False

    def install_python_packages(self, packages):
        """安装 Python 包"""
        try:
            progress = ProgressBar(len(packages), prefix='安装Python包:', suffix='完成')
            for i, package in enumerate(packages, 1):
                logger.info(f"正在安装 {package}...")
                try:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                 check=True, timeout=30,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    logger.warning("安装超时，尝试切换镜像源...")
                    if self._switch_mirror('pip'):
                        # 重试安装
                        subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                     check=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                progress.print_progress(i)
            return True
        except Exception as e:
            logger.error(f"安装 Python 包失败: {str(e)}")
            return False

    def install_java(self):
        """安装 Java"""
        try:
            if self.os_type == 'darwin':  # macOS
                subprocess.run(['brew', 'install', 'openjdk@11'], check=True)
            elif self.os_type == 'linux':
                subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'openjdk-11-jdk'], check=True)
            elif self.os_type == 'windows':
                # Windows 需要手动安装
                logger.info("请访问 https://adoptium.net/ 下载安装 Java JDK")
                return False
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"安装 Java 失败: {str(e)}")
            return False

    def install_android_sdk(self):
        """安装 Android SDK"""
        try:
            if self.os_type == 'darwin':  # macOS
                subprocess.run(['brew', 'install', 'android-commandlinetools'], check=True)
            elif self.os_type == 'linux':
                # Linux 需要手动安装
                logger.info("请访问 https://developer.android.com/studio 下载安装 Android SDK")
                return False
            elif self.os_type == 'windows':
                # Windows 需要手动安装
                logger.info("请访问 https://developer.android.com/studio 下载安装 Android SDK")
                return False
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"安装 Android SDK 失败: {str(e)}")
            return False

    def install_appium(self):
        """安装 Appium"""
        try:
            # 检查 Node.js 版本
            if self._check_command('node'):
                node_version = subprocess.run(['node', '-v'], 
                                           capture_output=True, 
                                           text=True).stdout.strip()
                if not node_version.startswith('v18'):
                    logger.error(f"当前 Node.js 版本 ({node_version}) 不兼容")
                    logger.error("Appium 需要 Node.js v18.x 版本")
                    
                    if self.os_type == 'darwin':
                        logger.info("您可以通过以下方式切换版本:")
                        logger.info("1. 使用 nvm 管理版本(推荐):")
                        logger.info("   - 安装 nvm: brew install nvm")
                        logger.info("   - 配置 nvm: 将以下内容添加到 ~/.zshrc 或 ~/.bash_profile:")
                        logger.info('     export NVM_DIR="$HOME/.nvm"')
                        logger.info('     [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \\. "/opt/homebrew/opt/nvm/nvm.sh"')
                        logger.info("   - 重新加载配置: source ~/.zshrc")
                        logger.info("   - 安装 Node.js: nvm install 18")
                        logger.info("   - 切换版本: nvm use node 18")
                        logger.info("2. 手动安装:")
                        logger.info("   - 访问: https://nodejs.org/download/release/latest-v18.x/")
                        logger.info("   - 下载并安装对应版本")
                        
                        choice = input("\n是否自动安装 nvm 并切换 Node.js? (y/n): ")
                        if choice.lower() == 'y':
                            # 安装 nvm
                            subprocess.run(['brew', 'install', 'nvm'], check=True)
                            
                            # 创建 nvm 目录
                            nvm_dir = os.path.expanduser("~/.nvm")
                            os.makedirs(nvm_dir, exist_ok=True)
                            
                            # 配置 nvm
                            shell_rc = os.path.expanduser("~/.zshrc")
                            if not os.path.exists(shell_rc):
                                shell_rc = os.path.expanduser("~/.bash_profile")
                            
                            # 检查配置是否已存在
                            with open(shell_rc, 'r') as f:
                                content = f.read()
                            
                            nvm_config = '''
                                # NVM configuration
                                export NVM_DIR="$HOME/.nvm"
                                [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"'''
                            
                            if 'NVM configuration' not in content:
                                with open(shell_rc, 'a') as f:
                                    f.write(nvm_config)
                            
                            logger.info("请在新终端中完成以下步骤后，重新运行环境检查：")
                            logger.info("1. 执行: source ~/.zshrc")
                            logger.info("2. 执行: nvm install node 18")
                            logger.info("3. 执行: nvm use node 18")
                            logger.info("4. 重新运行环境检查")
                            
                            return False
                        else:
                            return False
                    else:
                        return False
                else:
                    # 安装 Appium
                    subprocess.run(['npm', 'install', '-g', 'appium'], check=True)
                    return True
            else:
                logger.error("未找到 Node.js，请先安装 Node.js v18.x")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"安装 Appium 失败: {str(e)}")
            return False

    def _check_command(self, command):
        """检查命令是否存在"""
        try:
            subprocess.run([command, '--version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
            return True
        except:
            return False

    def install_webdriveragent(self):
        """安装 WebDriverAgent"""
        try:
            if self.os_type == 'darwin':  # 仅支持 macOS
                # 检查 Xcode 是否安装
                xcode_path = '/Applications/Xcode.app'
                if not os.path.exists(xcode_path):
                    logger.error("\n错误: 未检测到 Xcode")
                    logger.error("请先从 App Store 安装 Xcode，安装完成后重试")
                    logger.error("Xcode 下载地址: https://apps.apple.com/cn/app/xcode/id497799835")
                    logger.error("\n注意: Xcode 安装包较大(约 12GB)，下载和安装可能需要较长时间")
                    return False
                
                # 检查 Xcode 命令行工具
                try:
                    subprocess.run(['xcode-select', '-p'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 check=True)
                except subprocess.CalledProcessError:
                    logger.info("\n正在安装 Xcode 命令行工具...")
                    subprocess.run(['xcode-select', '--install'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
                
                # 安装其他依赖
                logger.info("\n安装 Carthage...")
                subprocess.run(['brew', 'install', 'carthage'], check=True)
                
                logger.info("\n安装 ios-deploy...")
                subprocess.run(['npm', 'install', '-g', 'ios-deploy'], check=True)
                
                # 设置 WebDriverAgent
                wda_path = os.path.join(os.path.expanduser('~'), 
                                      '.appium', 'node_modules', 'appium-xcuitest-driver', 
                                      'node_modules', 'appium-webdriveragent')
                
                if os.path.exists(wda_path):
                    logger.info("\n配置 WebDriverAgent...")
                    os.chdir(wda_path)
                    subprocess.run(['mkdir', '-p', 'Resources/WebDriverAgent.bundle'])
                    subprocess.run(['./Scripts/bootstrap.sh'], check=True)
                    return True
                else:
                    logger.error(f"\nWebDriverAgent 路径不存在: {wda_path}")
                    logger.error("请先安装 Appium 和 XCUITest 驱动")
                    return False
            else:
                logger.error("\nWebDriverAgent 仅支持 macOS 系统")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"\n安装 WebDriverAgent 失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"\n安装 WebDriverAgent 出错: {str(e)}")
            return False

    def setup_environment(self, missing_components):
        """设置环境"""
        results = {'success': [], 'failed': [], 'remaining': []}
        total_components = len(missing_components)
        progress = ProgressBar(total_components, prefix='环境配置:', suffix='完成')
        
        logger.info("\n开始安装缺失组件...")
        remaining_components = missing_components.copy()
        
        # 检查已安装组件
        if 'Android emulator' in remaining_components and self._check_android_tool('emulator'):
            logger.info("\n✓ Android emulator 已安装")
            remaining_components.remove('Android emulator')
            results['success'].append('Android emulator')
            
        if 'Android build-tools' in remaining_components and self._check_android_tool('aapt'):
            logger.info("\n✓ Android build-tools 已安装")
            remaining_components.remove('Android build-tools')
            results['success'].append('Android build-tools')

        # 处理剩余组件
        for i, component in enumerate(remaining_components, 1):
            logger.info(f"\n正在处理: {component}")
            success = False
            
            if 'pip install' in component:
                packages = component.split('pip install ')[1].split()
                if self.install_python_packages(packages):
                    results['success'].extend(packages)
                    success = True
                else:
                    results['failed'].extend(packages)
            
            elif 'Java JDK' in component:
                logger.info("安装 Java JDK...")
                if self.install_java():
                    results['success'].append('Java JDK')
                    success = True
                else:
                    results['failed'].append('Java JDK')
            
            elif 'Android' in component:
                logger.info(f"安装 {component}...")
                if self.install_android_sdk():
                    results['success'].append(component)
                    success = True
                else:
                    results['failed'].append(component)
            
            elif 'appium' in component.lower():
                logger.info(f"安装 {component}...")
                if self.install_appium():
                    results['success'].append(component)
                    success = True
                else:
                    results['failed'].append(component)
            
            elif 'WebDriverAgent' in component:
                logger.info("安装 WebDriverAgent...")
                if self.install_webdriveragent():
                    results['success'].append('WebDriverAgent')
                    success = True
                else:
                    results['failed'].append('WebDriverAgent')

            status = "✓" if success else "✗"
            logger.info(f"{status} {component}")
            progress.print_progress(i)

            # 如果安装成功就从剩余组件中移除
            if success:
                remaining_components = [x for x in remaining_components if x != component]

        # 为未成功安装的组件提供详细指南
        if results['failed']:
            logger.info("\n以下组件需要手动安装：")
            
            for component in results['failed']:
                logger.info(f"\n{component}:")
                
                if component == 'WebDriverAgent':
                    logger.info("1. 确保已安装 Xcode (从 App Store 安装)")
                    logger.info("2. 安装命令行工具: xcode-select --install")
                    logger.info("3. 安装依赖:")
                    logger.info("   brew install carthage")
                    logger.info("   npm install -g ios-deploy")
                    logger.info("4. 配置 WebDriverAgent:")
                    logger.info("   cd ~/.appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent")
                    logger.info("   mkdir -p Resources/WebDriverAgent.bundle")
                    logger.info("   ./Scripts/bootstrap.sh")
                    logger.info("详细说明: https://github.com/appium/WebDriverAgent#installation")
                
                elif 'appium-uiautomator2-driver' in component:
                    logger.info("1. 确保 Node.js v18 已正确安装:")
                    logger.info("   node -v  # 应显示 v18.x.x")
                    logger.info("2. 安装 Appium:")
                    logger.info("   npm install -g appium")
                    logger.info("3. 安装驱动:")
                    logger.info("   appium driver install uiautomator2")
                    logger.info("详细说明: https://github.com/appium/appium-uiautomator2-driver#installation")
                
                elif 'appium-xcuitest-driver' in component:
                    logger.info("1. 确保 Node.js v18 已正确安装:")
                    logger.info("   node -v  # 应显示 v18.x.x")
                    logger.info("2. 安装 Appium:")
                    logger.info("   npm install -g appium")
                    logger.info("3. 安装驱动:")
                    logger.info("   appium driver install xcuitest")
                    logger.info("详细说明: https://github.com/appium/appium-xcuitest-driver#installation")

        if results['success']:
            logger.info("\n以下组件已安装成功：")
            for component in results['success']:
                logger.info(f"  ✓ {component}")

        results['remaining'] = remaining_components
        return results

    def _check_android_tool(self, tool):
        """检查 Android 工具是否已安装"""
        android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        if not android_home:
            return False
            
        tool_paths = {
            'emulator': os.path.join(android_home, 'tools', 'emulator'),
            'aapt': os.path.join(android_home, 'build-tools', '*', 'aapt')
        }
        
        if tool in tool_paths:
            import glob
            return len(glob.glob(tool_paths[tool] + ('*' if self.os_type == 'windows' else ''))) > 0
        return False 