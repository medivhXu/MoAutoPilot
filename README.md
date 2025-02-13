# MoAutoPilot

MoAutoPilot 是一个基于 Appium 的移动端自动化测试框架，支持 Android、iOS 和 HarmonyOS 平台。

## ✨ 特性

- 🌈 多平台支持
  - Android 设备和模拟器
  - iOS 设备和模拟器
  - HarmonyOS 设备
- 🎯 智能化测试
  - 智能元素定位
  - 自动等待和重试
  - 自动处理权限弹窗
- 🔄 并行测试
  - 多设备并行执行
  - 失败重试机制
  - 用例优先级管理
- 📊 测试报告
  - HTML 格式报告
  - 失败场景截图
  - 详细执行日志

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 18/20
- Java JDK 8
- Android SDK (Android 测试)
- Xcode (iOS 测试)
- Appium 2.0+

### 安装步骤

1. 克隆项目并安装依赖
```bash
git clone https://github.com/yourusername/MoAutoPilot.git
cd MoAutoPilot
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. 配置测试环境
```bash
# 检查环境配置
python -m pytest tests/test_environment.py
```

3. 配置设备信息
```yaml
# config/config.yaml
devices:
  android:
    - deviceName: "Pixel_4"
      platformVersion: "11.0"
      app: "~/apps/demo.apk"

  ios:
    - deviceName: "iPhone 12"
      platformVersion: "14.5"
      app: "~/apps/demo.ipa"

  harmony:
    - platformName: HarmonyOS
      deviceName: Harmony Device
      platformVersion: '2.0'
      automationName: UiAutomator2
      appPackage: com.example.harmonyapp
      appActivity: .MainActivity
      noReset: true
```

### 运行测试

```bash
# 运行单个测试
pytest test_cases/test_login.py -v

# 并行测试
pytest test_cases/ -n auto

# 生成报告
pytest test_cases/ --html=report.html
```

## 📝 使用示例

### 测试用例编写

```python
from utils.appium_driver import AppiumDriver
from pages.login_page import LoginPage

def test_login():
    # 初始化驱动
    driver = AppiumDriver(platform='android')
    
    # 执行登录操作
    login_page = LoginPage(driver)
    login_page.login("username", "password")
    
    # 验证结果
    assert login_page.is_login_successful()
```

### 页面对象定义

```python
from utils.base_page import BasePage

class LoginPage(BasePage):
    # 页面元素
    username_input = "id=username"
    password_input = "id=password"
    login_button = "id=login"
    
    def login(self, username, password):
        self.input_text(self.username_input, username)
        self.input_text(self.password_input, password)
        self.click(self.login_button)
```

## 📖 文档

更多详细信息，请参考：
- [使用指南](docs/usage.md)
- [API 文档](docs/api.md)
- [最佳实践](docs/best-practices.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件

## 鸿蒙系统支持

MoAutoPilot 支持 HarmonyOS 设备的自动化测试。要测试鸿蒙设备，请确保：

1. 设备已开启开发者模式
2. 已安装必要的驱动
3. 在 `config/config.yaml` 中配置鸿蒙设备信息

示例配置：
```yaml
harmony:
  platformName: HarmonyOS
  deviceName: Harmony Device
  platformVersion: '2.0'
  automationName: UiAutomator2
  appPackage: com.example.harmonyapp
  appActivity: .MainActivity
  noReset: true
```

运行测试时，请设置环境变量：
```bash
export TEST_PLATFORM=harmony
pytest test_cases/test_automation.py
```