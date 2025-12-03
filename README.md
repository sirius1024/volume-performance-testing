# 虚拟机存储性能测试工具

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.6%2B-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey.svg)]()

一个专业的虚拟机存储性能测试工具，使用 DD 和 FIO 进行全面的存储系统性能评估和分析。当前支持 480 种 FIO 测试配置组合，提供详细的性能报告。

## 📋 目录

- [快速开始](#快速开始)
- [安装](#安装)
- [核心概览](#核心概览)
- [使用方法](#使用方法)
- [测试配置](#测试配置)
- [报告与归档](#报告与归档)
- [常见问题](#常见问题)

## 🚀 快速开始

### 快速测试场景（开发和验证）

适用于快速验证存储性能，测试时间短，资源消耗低：

```bash
# 克隆项目
git clone <repository-url>
cd volume-performance-testing

# 快速测试（推荐用于开发环境）
python3 main.py --quick

# 仅测试 FIO 随机 IO 性能
python3 main.py --fio-only --quick

# 仅测试 DD 顺序 IO 性能
python3 main.py --dd-only
```

**快速测试特点：**
- 测试时间：每个 FIO 测试 3 秒
- 测试场景：精选的代表性配置组合
- 总耗时：约 2-5 分钟
- 适用场景：功能验证、快速评估、CI/CD 流水线

### 生产使用场景（性能评估和基准测试）

适用于生产环境性能评估，提供全面准确的性能数据：

```bash
# 生产级完整测试（推荐）
python3 main.py --runtime 60 --cleanup

# 高精度 FIO 测试
python3 main.py --fio-only --runtime 120

# 自定义测试目录和报告
python3 main.py --test-dir /mnt/nvme --output nvme_report.md --runtime 60

# 查看测试配置信息
python3 main.py --fio-info
```

**生产测试特点：**
- 测试时间：每个 FIO 测试 60-120 秒
- 测试场景：480 种完整配置组合
- 总耗时：约 8-16 小时（完整测试）
- 适用场景：性能基准测试、容量规划、硬件选型

## 📦 安装

### 系统要求

- Python 3.6+
- FIO (Flexible I/O Tester)
- 至少 2GB 可用磁盘空间

### 安装依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install fio python3 python3-pip

# CentOS/RHEL
sudo yum install fio python3 python3-pip
# 或使用 dnf (较新版本)
sudo dnf install fio python3 python3-pip

# macOS (使用 Homebrew)
brew install fio python3
```

### 验证安装

```bash
# 检查 FIO 版本
fio --version

# 检查 Python 版本
python3 --version

# 测试工具是否正常工作
python3 main.py --fio-info
```

## 核心概览

- 测试类型：DD（顺序读写）、FIO（随机读/写/混合）
- FIO矩阵：块大小×队列深度×并发×读写比例，共 480 场景
- 目录归档：报告统一写入 `test_dir/reports/<时间戳>/`
- 快速模式：报告文件名追加 `-quick`

## 🔧 使用方法

### 基本用法

```bash
# 运行所有测试（默认）
python3 main.py

# 等价于
python3 main.py --all
```

### 选择测试类型

```bash
# 仅运行 DD 测试
python3 main.py --dd-only

# 仅运行 FIO 测试
python3 main.py --fio-only

# 运行所有测试
python3 main.py --all
```

### 自定义测试参数

```bash
# 自定义测试时间
python3 main.py --runtime 30

# 自定义测试目录
python3 main.py --test-dir /tmp/storage_test

# 自定义报告文件
python3 main.py --output my_report.md

# 测试完成后清理文件
python3 main.py --cleanup
```

### 独立模块使用

```bash
# 单独运行 DD 测试
python3 dd_test.py --test-dir /tmp/test --cleanup

# 单独运行 FIO 测试
python3 fio_test.py --runtime 10 --cleanup

# FIO 快速测试
python3 fio_test.py --quick --runtime 1
```

## ⚙️ 参数说明

### main.py 主控脚本参数

| 参数 | 类型 | 默认值 | 说明 | 推荐场景 |
|------|------|--------|------|----------|
| `--all` | flag | `True`* | 运行所有测试（DD + FIO） | 完整性能评估 |
| `--dd-only` | flag | `False` | 仅运行 DD 测试 | 顺序 IO 性能测试 |
| `--fio-only` | flag | `False` | 仅运行 FIO 测试 | 随机 IO 性能测试 |
| `--fio-info` | flag | `False` | 显示 FIO 测试矩阵信息 | 了解测试配置 |
| `--test-dir` | string | `./test_data` | 测试数据目录 | 指定测试存储位置 |
| `--runtime` | int | `3` | FIO 每个测试运行时间（秒） | 快速测试: 3-10, 生产: 60-120 |
| `--quick` | flag | `False` | 快速测试模式 | 开发验证、CI/CD |
| `--cleanup` | flag | `False` | 测试完成后清理测试文件 | 生产环境、磁盘空间有限 |
| `--output` | string | 自动生成 | 指定报告输出文件路径 | 自定义报告位置 |

*注：如果不指定测试类型，默认运行 `--all`

### 独立模块参数

#### dd_test.py 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--test-dir` | string | `./test_data` | 测试数据目录 |
| `--cleanup` | flag | `False` | 测试完成后清理测试文件 |

#### fio_test.py 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--test-dir` | string | `./test_data` | 测试数据目录 |
| `--runtime` | int | `3` | FIO 测试时间（秒） |
| `--quick` | flag | `False` | 快速测试模式 |
| `--cleanup` | flag | `False` | 测试完成后清理测试文件 |
| `--info` | flag | `False` | 显示测试配置信息 |

### 参数使用建议

#### 开发和测试环境
```bash
# 快速验证
python3 main.py --quick --cleanup

# 功能测试
python3 main.py --runtime 10 --cleanup
```

#### 生产环境评估
```bash
# 标准性能测试
python3 main.py --runtime 60 --cleanup

# 高精度基准测试
python3 main.py --runtime 120 --test-dir /mnt/target_storage
```

#### CI/CD 集成
```bash
# 自动化测试
python3 main.py --quick --cleanup --output ci_report.md
```

## 📁 项目结构

```
volume-performance-testing/
├── main.py                    # 主控脚本，统一入口
├── dd_test.py                 # DD 测试模块
├── fio_test.py                # FIO 测试模块
├── common.py                  # 共享工具类和数据结构
├── generate_fio_commands.py   # FIO 命令生成工具
├── fio_test.md               # FIO 测试详细说明
├── README.md                 # 项目文档
├── LICENSE                   # 开源许可证
├── .gitignore               # Git 忽略文件配置
└── test_data/
    └── reports/
        └── YYYYMMDD_HHMMSS/
            ├── storage_performance_report_YYYYMMDD_HHMMSS[ -quick ].md
            └── fio_detailed_report[ -quick ].md
```

### 核心模块说明

#### main.py - 主控脚本
- **功能**：提供统一的命令行接口，协调各个测试模块
- **核心类**：
  - `StoragePerformanceTest`：主测试控制器
  - `ReportGenerator`：报告生成器
- **职责**：参数解析、测试流程控制、结果汇总

#### dd_test.py - DD 测试模块
- **功能**：使用 dd 命令进行顺序读写性能测试
- **核心类**：`DDTestRunner`
- **测试类型**：
  - 顺序写入测试（1M、4K、1G 块大小）
  - 顺序读取测试（1M、4K、1G 块大小）
- **输出指标**：吞吐量 (MB/s)

#### fio_test.py - FIO 测试模块
- **功能**：使用 FIO 进行随机 IO 性能测试
- **核心类**：`FIOTestRunner`
- **测试矩阵**：480 种配置组合
  - 8 种块大小：4K/8K/16K/32K/64K/128K/1M/4M
  - 6 种队列深度：1/2/4/8/16/32
  - 智能并发数映射（qd=32 → 4, 8）
  - 5 种读写比例：0%/25%/50%/75%/100% 读
- **输出指标**：IOPS、延迟 (μs)、吞吐量 (MB/s)

#### common.py - 共享工具类
- **功能**：提供通用的工具类和数据结构
- **核心类**：
  - `TestResult`：测试结果数据结构
  - `Logger`：日志记录器
  - `SystemInfoCollector`：系统信息收集器
- **工具函数**：目录管理、文件操作等

### 代码架构

```
┌─────────────────┐
│    main.py      │  ← 用户入口
│  (主控脚本)      │
└─────────┬───────┘
          │
          ├─────────────────┬─────────────────
          │                 │
┌─────────▼───────┐ ┌───────▼───────┐
│   dd_test.py    │ │  fio_test.py  │
│   (DD测试)      │ │  (FIO测试)    │
└─────────┬───────┘ └───────┬───────┘
          │                 │
          └─────────┬───────┘
                    │
          ┌─────────▼───────┐
          │   common.py    │
          │   (共享工具)    │
          └─────────────────┘
```

### 开发指南（精简）

#### 添加/修改测试
- 在 `fio_test.py`/`dd_test.py` 调整矩阵或参数
- 在 `main.py` 集成与汇总输出
- 使用 `tools/dump_commands.py` 生成命令清单验证

#### 代码风格
- Python 3.6+，PEP 8，类型注解

## 🧪 测试配置

### FIO 测试矩阵（480 种配置）

#### 测试参数组合

- **块大小**：4K, 8K, 16K, 32K, 64K, 128K, 1M, 4M（8种）
- **队列深度**：1, 2, 4, 8, 16, 32（6种）
- **并发数**：根据队列深度智能映射（2种配置/队列深度）
- **读写比例**：0%, 25%, 50%, 75%, 100% 读（5种）

#### 队列深度与并发数映射

| 队列深度 | 并发数选项 | 适用场景 |
|----------|------------|----------|
| 1-4 | 1, 4 | 单线程和轻度并发 |
| 8-16 | 4, 8 | 中等并发负载 |
| 32     | 4, 8      | 高并发负载 |

#### 测试类型说明

- **randread**：100% 随机读
- **randwrite**：100% 随机写
- **randrw**：随机读写混合（25%/50%/75% 读比例）

### DD 测试配置（已过滤 bs < 32K）

- **顺序写入**：1G, 1M, 64K, 32K
- **顺序读取**：1G, 1M, 64K, 32K
- **测试文件大小**：1GB

## 报告与归档

### 报告文件

- 综合报告与详细报告将归档到 `test_dir/reports/<时间戳>/` 目录：
  - `storage_performance_report_<YYYYMMDD_HHMMSS>[ -quick ].md`：综合测试报告
  - `fio_detailed_report[ -quick ].md`：FIO 详细测试结果
- `storage_test.log`：详细执行日志（位于 `test_dir` 根目录）

> 说明：`test_dir` 为构造测试文件与日志所在目录（默认 `./test_data`）。报告统一保存在其子目录 `reports/<时间戳>/`，便于后续批次比对。

### 关键指标
- DD：吞吐量 (MB/s)、测试时间 (秒)
- FIO：IOPS、延迟 (μs)、吞吐量 (MB/s)、P99 延迟

### 性能评估标准

#### SSD 性能参考值
- **随机读 IOPS**：> 10,000（优秀），> 5,000（良好）
- **随机写 IOPS**：> 8,000（优秀），> 3,000（良好）
- **顺序读写**：> 500 MB/s（优秀），> 200 MB/s（良好）

#### HDD 性能参考值
- **随机读 IOPS**：> 150（优秀），> 80（良好）
- **随机写 IOPS**：> 120（优秀），> 60（良好）
- **顺序读写**：> 150 MB/s（优秀），> 80 MB/s（良好）

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork 项目**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建 Pull Request**

### 开发环境设置

```bash
# 克隆你的 fork
git clone https://github.com/yourusername/volume-performance-testing.git
cd volume-performance-testing

# 安装依赖
sudo apt-get install fio python3

# 运行测试验证环境
python3 main.py --quick
```

### 代码贡献规范

- 遵循现有代码风格
- 添加适当的注释和文档
- 确保新功能有相应的测试
- 更新相关文档

### 报告问题

如果发现 bug 或有功能建议，请创建 Issue 并包含：

- 详细的问题描述
- 复现步骤
- 系统环境信息
- 相关日志输出

### 功能请求

我们特别欢迎以下类型的贡献：

- 新的存储测试工具集成
- 性能分析和可视化功能
- 测试报告格式扩展
- 性能优化建议
- 文档改进

## ❓ 常见问题

### Q: 测试失败，提示 "fio: command not found"
**A**: 需要安装 FIO 工具：
```bash
sudo apt-get install fio  # Ubuntu/Debian
sudo yum install fio      # CentOS/RHEL
```

### Q: 如何选择合适的测试时间？
**A**: 
- **快速验证**：3-10 秒
- **标准测试**：30-60 秒
- **生产基准**：120 秒或更长

### Q: 测试结果如何解读？
**A**: 
- **IOPS**：越高越好，关注随机访问性能
- **延迟**：越低越好，特别关注 P99 延迟
- **吞吐量**：顺序访问的重要指标

### Q: 可以在生产环境运行吗？
**A**: 
- **快速模式**：相对安全，建议维护窗口运行
- **完整测试**：会产生大量 I/O，谨慎使用
- **建议**：先在测试环境验证

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目：

- [FIO](https://github.com/axboe/fio) - Flexible I/O Tester
- [Python](https://www.python.org/) - 编程语言

---

**如果这个项目对你有帮助，请给我们一个 ⭐️！**
