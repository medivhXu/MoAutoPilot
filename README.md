# Mobile UI 自动化测试框架

基于 Appium 的移动端自动化测试框架，支持 Android 和 iOS 平台。

## 特性

- 支持 Android 和 iOS 平台
- 基于 Page Object Model (POM) 设计模式
- 支持 Docker 部署
- 集成 Appium 服务
- 支持并行测试
- 自动生成 HTML 测试报告
- 日志管理系统
- 配置文件集中管理

## 目录结构

```
.
├── config/
│   └── config.yaml          # 配置文件
├── pages/
│   ├── __init__.py
│   ├── android/            # Android 页面对象
│   │   └── __init__.py
│   ├── ios/               # iOS 页面对象
│   │   └── __init__.py
│   └── base_page.py       # 基础页面类
├── test_cases/
│   ├── __init__.py
│   └── test_login.py      # 测试用例
├── utils/
│   ├── __init__.py
│   ├── appium_driver.py   # Appium 驱动管理
│   └── logger.py          # 日志工具
├── test_data/             # 测试数据
├── logs/                  # 日志文件
├── reports/               # 测试报告
├── requirements.txt       # Python 依赖
├── Dockerfile            # Docker 构建文件
├── docker-compose.yml    # Docker 编排文件
└── README.md
```

## 环境要求

- Python 3.9+
- Appium Server
- Android SDK (适用于 Android 测试)
- Xcode (适用于 iOS 测试)
- Docker & Docker Compose (可选)

## 安装

### 本地安装

1. 克隆项目：
```bash
git clone <repository_url>
cd <project_directory>
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

### Docker 部署

1. 启动 Appium 服务：
```bash
docker-compose up -d
```

2. 启动测试：
```bash
pytest
```

3. 生成测试报告：
```bash
pytest --html=report.html
```

## 配置

### 配置文件

配置文件集中管理在 `config` 目录下，支持多个环境配置。

### 测试环境配置
```bash
pytest --config=config/test.yaml
```

### 生产环境配置
```bash
pytest --config=config/production.yaml
```

## 运行测试

### 本地运行测试
```bash
# 运行所有测试
pytest test_cases/

# 运行特定测试文件
pytest test_cases/test_login.py

# 生成 HTML 报告
pytest test_cases/ --html=reports/report.html
```

### Docker 环境运行
```bash
# 运行所有测试
docker-compose run test

# 查看日志
docker-compose logs -f
```

## 环境检查

运行环境检查和安装：

```bash
# 使用 -s 参数允许输入输出交互
pytest test_cases/test_automation.py -v -s


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
    