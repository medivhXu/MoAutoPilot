# MoAutoPilot

MoAutoPilot 是一个强大的移动端 UI 自动化测试框架，基于 Appium 构建，支持 Android、iOS 和 HarmonyOS 平台。

## ✨ 核心特性

- 🌈 全平台支持：Android、iOS 和 HarmonyOS
- 🎯 智能元素定位：自动分析和定位 UI 元素
- 🔄 并行测试：支持多设备并行测试
- 📊 自动报告：生成详细的 HTML 测试报告
- 🛠️ 环境管理：自动检测和配置测试环境
- 🎨 POM 设计：基于 Page Object Model 模式
- 🐳 容器支持：提供 Docker 部署方案

## 🚀 快速开始

### 环境准备

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/MoAutoPilot.git
cd MoAutoPilot

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行环境检查
pytest test_cases/test_automation.py -v -s
```


注意：
- 首次运行会检查并安装必要组件
- 需要手动安装的组件会提示确认
- 环境配置完成后会保存状态
- 后续运行会复用已有环境

## 页面对象示例

```python
from pages.base_page import BasePage
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    # 定义页面元素
    username_input = (By.ID, "username_field")
    password_input = (By.ID, "password_field")
    login_button = (By.ID, "login_button")

    def login(self, username, password):
        """登录方法"""
        self.input_text(self.username_input, username)
        self.input_text(self.password_input, password)
        self.click(self.login_button)
```

## 测试用例示例

```python
from utils.appium_driver import AppiumDriver
from pages.login_page import LoginPage

class TestLogin:
    def setup_class(self):
        self.driver = AppiumDriver().init_driver()
        self.login_page = LoginPage(self.driver)

    def test_login_success(self):
        self.login_page.login("username", "password")
        # 添加断言...

    def teardown_class(self):
        self.driver.quit()
```

## 日志系统

日志文件保存在 `logs` 目录下，按日期自动生成：

```python
from utils.logger import Logger

logger = Logger().get_logger()
logger.info("测试开始")
logger.error("发生错误")
```

## 常见问题解决

### 1. Appium 连接问题
- 检查 Appium 服务是否正常运行
- 确认设备已正确连接并启用调试模式
- 验证配置文件中的连接参数

### 2. 元素定位失败
- 检查定位方式是否正确
- 确认等待时间是否充足
- 验证页面是否已完全加载

### 3. Docker 相关问题
- 确保 Docker 服务正常运行
- 检查端口映射配置
- 验证容器网络连接

## 最佳实践

1. 测试用例编写
   - 遵循单一职责原则
   - 保持测试用例独立性
   - 合理使用夹具（fixtures）

2. 页面对象维护
   - 及时更新页面元素定位
   - 封装常用操作
   - 保持代码简洁

3. 配置管理
   - 不同环境使用不同配置文件
   - 敏感信息使用环境变量
   - 定期更新配置参数

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或联系维护团队。
    