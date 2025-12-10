# 贡献指南

感谢你对 **Volume Performance Testing** 项目的兴趣！我们欢迎任何形式的贡献，包括提交 Bug、改进文档、增加新功能或优化现有代码。

为了让协作更加顺畅，请在贡献前阅读以下指南。

## 🛠 开发环境设置

### 前置要求
- **Python**: 3.6 或更高版本
- **FIO**: 需要安装 `fio` 命令行工具
- **操作系统**: Linux (推荐) 或 macOS

### 快速上手
1. **Fork 本仓库**：点击右上角的 Fork 按钮。
2. **克隆代码**：
   ```bash
   git clone https://github.com/YOUR_USERNAME/volume-performance-testing.git
   cd volume-performance-testing
   ```
3. **运行测试验证环境**：
   ```bash
   # 运行快速测试，确保环境正常
   python3 main.py --quick --cleanup
   ```

## 📂 代码结构说明

本项目采用模块化设计，主要包含以下部分：

- **核心逻辑**：
  - `main.py`: 程序入口，负责参数解析和流程控制。
  - `dd_test.py`: 封装 DD 测试逻辑。
  - `fio_test.py`: 封装 FIO 测试逻辑，包括矩阵生成和结果解析。
  - `report_generator.py`: 负责生成 Markdown 和 JSON 报告。
  - `config_loader.py`: 统一加载集群配置。
  - `core_scenarios_loader.py`: 加载自定义的核心测试场景 (JSON)。

- **通用模块** (`utils/` & `models/`)：
  - `models/result.py`: 定义 `TestResult` 数据类，确保结果格式统一。
  - `utils/logger.py`: 日志工具。
  - `utils/system_info.py`: 系统信息收集。
  - `utils/file_utils.py`: 文件和目录操作。

- **工具脚本** (`tools/`):
  - `dispatch.py`, `collect.py`, `aggregate.py`: 用于集群 (3pNv) 测试流程。
  - `dump_commands.py`: 导出所有生成的测试命令，用于审计或手动执行。

## 📐 编码规范

1. **Python 版本**：代码应兼容 Python 3.6+。
2. **风格**：遵循 PEP 8 编码风格。
   - 使用 4 个空格缩进。
   - 变量命名清晰（如 `throughput_mbps` 而非 `speed`）。
3. **类型注解**：鼓励在函数参数和返回值上添加类型注解（Type Hints）。
4. **导入**：避免循环导入。尽量使用绝对导入。

## 📝 提交规范

1. **Commit Message**：应清晰描述更改内容。
   - `feat: 添加 xxx 功能`
   - `fix: 修复 xxx 问题`
   - `docs: 更新文档`
   - `refactor: 重构 xxx 模块`
2. **Pull Request**：
   - 标题简洁明了。
   - 描述中说明变更的背景和测试方法。
   - 如果修复了 Issue，请关联 Issue ID。

## 🧪 测试你的更改

在提交 PR 之前，请务必运行以下命令，确保没有破坏现有功能：

1. **本地回归测试**：
   ```bash
   python3 main.py --quick --cleanup
   ```
   确保所有测试通过 (PASS)，且生成的报告无误。

2. **验证工具脚本**（如果修改了工具）：
   - 尝试运行 `python3 tools/dump_commands.py` 确保命令生成逻辑正常。

## 💡 添加新功能指引

### 如果你想添加新的 FIO 测试场景：
- 修改 `fio_test.py` 中的 `FIOTestRunner._generate_test_matrix` 方法。
- 或者在 `config/core_scenarios.json` 中添加自定义场景（无需修改代码）。

### 如果你想改进报告格式：
- 修改 `report_generator.py` 中的 `ReportGenerator` 类。

### 如果你想支持新的测试工具：
- 参考 `dd_test.py` 的结构，创建一个新的 `xxx_test.py`，并在 `main.py` 中注册。

---
再次感谢你的贡献！🚀
