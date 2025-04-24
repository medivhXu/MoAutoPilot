# MoAutoPilot

MoAutoPilot 是一个基于 Appium 的移动端自动化测试框架，支持 Android、iOS 和 HarmonyOS 平台，并集成了 AI 驱动的测试用例生成能力。

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
- 🤖 AI 驱动测试
  - 基于 LLM 的测试用例生成
  - 智能 UI 分析和交互
  - 自适应测试策略

## 🔍 与其他自动化测试框架的区别

MoAutoPilot 在传统移动自动化测试框架的基础上进行了多项创新：

| 特性 | MoAutoPilot | 传统自动化框架 |
|------|------------|---------------|
| **测试用例生成** | AI 驱动自动生成 | 手动编写 |
| **元素定位** | 智能定位，多策略自动切换 | 固定定位策略 |
| **平台支持** | Android、iOS、HarmonyOS | 通常仅支持 Android 和 iOS |
| **测试策略** | 自适应测试策略，基于 AI 分析 | 固定测试策略 |
| **维护成本** | 低（自动适应 UI 变化） | 高（UI 变化需手动更新） |
| **测试覆盖率** | 高（AI 可探索边缘场景） | 中（仅覆盖预定义场景） |
| **执行效率** | 高（并行执行，智能重试） | 中（常规执行策略） |

### 核心优势

1. **AI 驱动的测试用例生成**：无需手动编写大量测试用例，AI 可基于应用描述自动生成全面的测试场景
2. **智能 UI 分析**：自动分析应用界面结构，识别关键交互元素
3. **跨平台兼容性**：一套框架同时支持三大移动平台，包括新兴的鸿蒙系统
4. **自适应测试执行**：根据测试结果动态调整测试策略，提高测试效率
5. **低维护成本**：自动适应 UI 变化，减少维护工作量

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 18/20
- Java JDK 8
- Android SDK (Android 测试)
- Xcode (iOS 测试)
- Appium 2.0+
- Ollama (AI 测试用例生成)

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

2. 安装 Ollama（用于 AI 测试用例生成）
```bash
# macOS
curl -fsSL https://ollama.com/install.sh | sh

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 从 https://ollama.com/download 下载安装包
```

3. 下载 LLM 模型（推荐使用 deepseek 系列模型）
```bash
ollama pull deepseek-r1:8b
# 或使用更大参数的模型以获得更好效果
ollama pull deepseek-r1:14b
```

4. 配置测试环境
```bash
# 检查环境配置
python -m pytest tests/test_environment.py -v -s
```

5. 配置设备信息
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

## 🤖 AI 测试用例生成

MoAutoPilot 集成了基于大型语言模型的测试用例生成功能，可以根据应用描述自动生成测试用例。

### 配置 AI 测试用例生成

1. 确保 Ollama 服务已启动
```bash
# 检查 Ollama 服务状态
curl http://localhost:11434/api/tags
```

2. 准备测试用例描述文件

在 `test_cases_source` 目录下创建 Markdown 文件，描述应用功能和测试需求：

```markdown
# 短视频应用测试需求

## 功能描述
短视频应用允许用户浏览、上传、编辑和分享短视频内容。

## 测试范围
- 视频浏览功能
- 视频上传功能
- 用户互动功能（点赞、评论、分享）
- 账户管理功能
```

### 生成测试用例

运行测试用例生成脚本：

```bash
python -m pytest test_cases/test_automation.py::TestAutomation::load_test_cases_from_source -v -s
```

生成的测试用例将保存在 `gen_cases` 目录下，格式为 JSON 或 Markdown。

### 自定义 AI 提示模板

您可以根据需要自定义 AI 提示模板，以生成更符合特定需求的测试用例：

```python
# 在 test_automation.py 中修改 prompt 模板
prompt = f"""你是一个专注移动APP测试的专家，请针对{应用类型}APP特性生成用例，按JSON格式输出：\
            {content}
            要求包含：测试步骤、预期结果、优先级。
            特别注意：
                1. {特定关注点1}
                2. {特定关注点2}
                3. {特定关注点3}"""
```

### 使用 LangChain 框架（可选）

MoAutoPilot 也支持使用 LangChain 框架进行更灵活的 AI 测试用例生成：

```python
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

template = """作为资深测试工程师，请为{feature}生成测试用例：
1. 包含{normal_count}个正常场景和{error_count}个异常场景
2. 每个用例需有明确的前置条件
3. 输出Markdown表格格式"""

prompt = PromptTemplate.from_template(template)
llm = Ollama(model="deepseek-r1:14b", temperature=0.5)

chain = prompt | llm
response = chain.invoke({
    "feature": "抖音视频上传功能",
    "normal_count": 3,
    "error_count": 2
})
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

### 运行测试

```bash
# 运行单个测试
pytest test_cases/test_automation.py -v -s

# 并行测试
pytest test_cases/ -n auto

# 生成报告
pytest test_cases/ --html=report.html
```

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