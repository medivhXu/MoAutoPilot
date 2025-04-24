# MoAutoPilot

MoAutoPilot is a mobile automation testing framework based on Appium, supporting Android, iOS, and HarmonyOS platforms, with integrated AI-driven test case generation capabilities.

## ✨ Features

- 🌈 Multi-platform Support
  - Android devices and emulators
  - iOS devices and emulators
  - HarmonyOS devices
- 🎯 Intelligent Testing
  - Smart element location
  - Automatic waiting and retry
  - Automatic permission dialog handling
- 🔄 Parallel Testing
  - Multi-device parallel execution
  - Failure retry mechanism
  - Test case priority management
- 📊 Test Reports
  - HTML format reports
  - Failed scenario screenshots
  - Detailed execution logs
- 🤖 AI-driven Testing
  - LLM-based test case generation
  - Intelligent UI analysis and interaction
  - Adaptive testing strategies

## 🔍 Differences from Other Automation Testing Frameworks

MoAutoPilot has made several innovations based on traditional mobile automation testing frameworks:

| Feature | MoAutoPilot | Traditional Automation Frameworks |
|---------|------------|-----------------------------------|
| **Test Case Generation** | AI-driven automatic generation | Manual writing |
| **Element Location** | Intelligent location, multiple strategies with automatic switching | Fixed location strategies |
| **Platform Support** | Android, iOS, HarmonyOS | Usually only Android and iOS |
| **Testing Strategy** | Adaptive testing strategies based on AI analysis | Fixed testing strategies |
| **Maintenance Cost** | Low (automatically adapts to UI changes) | High (UI changes require manual updates) |
| **Test Coverage** | High (AI can explore edge cases) | Medium (only covers predefined scenarios) |
| **Execution Efficiency** | High (parallel execution, intelligent retry) | Medium (regular execution strategies) |

### Core Advantages

1. **AI-driven Test Case Generation**: No need to manually write numerous test cases, AI can automatically generate comprehensive test scenarios based on application descriptions
2. **Intelligent UI Analysis**: Automatically analyze application interface structure, identify key interactive elements
3. **Cross-platform Compatibility**: One framework supports all three major mobile platforms, including the emerging HarmonyOS
4. **Adaptive Test Execution**: Dynamically adjust testing strategies based on test results, improving testing efficiency
5. **Low Maintenance Cost**: Automatically adapt to UI changes, reducing maintenance workload

## 🚀 Quick Start

### Requirements

- Python 3.8+
- Node.js 18/20
- Java JDK 8
- Android SDK (for Android testing)
- Xcode (for iOS testing)
- Appium 2.0+
- Ollama (for AI test case generation)

### Installation Steps

1. Clone the project and install dependencies
```bash
git clone https://github.com/yourusername/MoAutoPilot.git
cd MoAutoPilot
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. Install Ollama (for AI test case generation)
```bash
# macOS
curl -fsSL https://ollama.com/install.sh | sh

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download the installer from https://ollama.com/download
```

3. Download LLM model (recommended to use deepseek series models)
```bash
ollama pull deepseek-r1:8b
# or use a larger parameter model for better results
ollama pull deepseek-r1:14b
```

4. Configure the test environment
```bash
# Check environment configuration
python -m pytest tests/test_environment.py -v -s
```

5. Configure device information
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

## 🤖 AI Test Case Generation

MoAutoPilot integrates test case generation functionality based on large language models, which can automatically generate test cases according to application descriptions.

### Configure AI Test Case Generation

1. Ensure the Ollama service is running
```bash
# Check Ollama service status
curl http://localhost:11434/api/tags
```

2. Prepare test case description file

Create a Markdown file in the `test_cases_source` directory, describing the application functionality and testing requirements:

```markdown
# Short Video Application Testing Requirements

## Functional Description
The short video application allows users to browse, upload, edit, and share short video content.

## Testing Scope
- Video browsing functionality
- Video upload functionality
- User interaction functionality (like, comment, share)
- Account management functionality
```

### Generate Test Cases

Run the test case generation script:

```bash
python -m pytest test_cases/test_automation.py::TestAutomation::load_test_cases_from_source -v -s
```

Generated test cases will be saved in the `gen_cases` directory, in JSON or Markdown format.

### Customize AI Prompt Templates

You can customize AI prompt templates according to your needs to generate test cases that better meet specific requirements:

```python
# Modify the prompt template in test_automation.py
prompt = f"""You are an expert focused on mobile APP testing, please generate test cases for {app_type} APP features, output in JSON format:\
            {content}
            Requirements include: test steps, expected results, priority.
            Special attention:
                1. {specific_focus_point1}
                2. {specific_focus_point2}
                3. {specific_focus_point3}"""
```

### Using LangChain Framework (Optional)

MoAutoPilot also supports using the LangChain framework for more flexible AI test case generation:

```python
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

template = """As a senior test engineer, please generate test cases for {feature}:
1. Include {normal_count} normal scenarios and {error_count} error scenarios
2. Each case needs clear preconditions
3. Output in Markdown table format"""

prompt = PromptTemplate.from_template(template)
llm = Ollama(model="deepseek-r1:14b", temperature=0.5)

chain = prompt | llm
response = chain.invoke({
    "feature": "TikTok video upload functionality",
    "normal_count": 3,
    "error_count": 2
})
```

## 📝 Usage Examples

### Test Case Writing

```python
from utils.appium_driver import AppiumDriver
from pages.login_page import LoginPage

def test_login():
    # Initialize driver
    driver = AppiumDriver(platform='android')
    
    # Perform login operation
    login_page = LoginPage(driver)
    login_page.login("username", "password")
    
    # Verify results
    assert login_page.is_login_successful()
```

### Page Object Definition

```python
from utils.base_page import BasePage

class LoginPage(BasePage):
    # Page elements
    username_input = "id=username"
    password_input = "id=password"
    login_button = "id=login"
    
    def login(self, username, password):
        self.input_text(self.username_input, username)
        self.input_text(self.password_input, password)
        self.click(self.login_button)
```

### Running Tests

```bash
# Run a single test
pytest test_cases/test_automation.py -v -s

# Parallel testing
pytest test_cases/ -n auto

# Generate report
pytest test_cases/ --html=report.html
```

## 🤝 Contribution

Issues and Pull Requests are welcome.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## HarmonyOS Support

MoAutoPilot supports automated testing of HarmonyOS devices. To test HarmonyOS devices, ensure:

1. Developer mode is enabled on the device
2. Necessary drivers are installed
3. HarmonyOS device information is configured in `config/config.yaml`

Example configuration:
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

When running tests, set the environment variable:
```bash
export TEST_PLATFORM=harmony
pytest test_cases/test_automation.py
```