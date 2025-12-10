# 虚拟机存储性能测试工具

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.6%2B-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey.svg)]()

一个专业的虚拟机存储性能测试工具，使用 DD 和 FIO 进行全面的存储系统性能评估和分析。当前支持 480 种 FIO 测试配置组合，提供详细的性能报告，并支持多机集群测试与结果聚合。

## 📋 目录

- [快速开始](#-快速开始)
- [核心功能](#-核心功能)
- [使用方法](#-使用方法)
- [集群测试 (3pNv)](#-集群测试-3pnv)
- [参数说明](#%EF%B8%8F-参数说明)
- [测试指标](#-测试指标)
- [项目结构](#-项目结构)
- [常见问题](#-常见问题)

## � 安装要求

在开始之前，请确保您的环境已安装以下依赖。

### 1. 基础依赖（本地测试必须）

所有运行测试的机器（包括控制端和被测端）都需要安装：

- **Python 3.6+**
- **FIO** (Flexible I/O Tester)

#### 安装命令
```bash
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y python3 fio

# CentOS / RHEL
sudo yum install -y python3 fio
```

### 2. 集群测试依赖（仅控制端需要）

如果您计划运行多机集群测试 (`3pNv`)，且在 `cluster.json` 中使用**密码认证**（而非密钥），则控制端必须安装 `sshpass`。

```bash
# Ubuntu / Debian
sudo apt-get install -y sshpass

# CentOS / RHEL
sudo yum install -y sshpass
```
> **注意**：如果使用 SSH 密钥认证（推荐），则无需安装 `sshpass`。

## �🚀 快速开始

### 1. 快速验证（开发环境）
适用于快速验证环境和工具是否正常，测试时间短（每项 3 秒）：

```bash
git clone <repository-url>
cd volume-performance-testing

# 运行快速测试并清理生成的文件
python3 main.py --quick --cleanup
```

### 2. 生产评估（基准测试）
适用于生产环境性能评估，提供全面准确的性能数据：

```bash
# 完整测试（推荐，每项 60 秒）
python3 main.py --runtime 60 --cleanup

# 仅测试 FIO 随机 IO 性能
python3 main.py --fio-only --runtime 60
```

## 🌟 核心功能

- **全面覆盖**：
  - **DD**：顺序读写吞吐量测试。
  - **FIO**：480 种场景组合（块大小 × 队列深度 × 并发 × 读写比例）。
- **智能策略**：
  - 自动检测文件系统。
  - 在 `9p` 文件系统上自动回退 FIO 引擎配置。
  - 自动处理并发数与队列深度的映射。
- **报告生成**：
  - 自动生成 Markdown 格式的综合报告和详细报告。
  - 支持 JSON 格式的原始数据输出，便于二次开发。
- **集群支持**：
  - 支持多机并发测试下发。
  - 支持多机结果自动归集与聚合。

## 🔧 使用方法

### 基本命令

```bash
# 运行所有测试（默认）
python3 main.py

# 仅运行 DD 测试
python3 main.py --dd-only

# 仅运行 FIO 测试
python3 main.py --fio-only
```

### 自定义参数

```bash
# 自定义测试时长（秒）
python3 main.py --runtime 30

# 自定义测试目录
python3 main.py --test-dir /mnt/nvme_disk

# 自定义报告输出路径
python3 main.py --output my_report.md

# 查看 FIO 测试矩阵信息
python3 main.py --fio-info
```

## 🌐 集群测试 (3pNv)

本项目支持在多台虚拟机上同时运行测试，并聚合结果，适用于评估存储集群的整体性能。

### 1. 配置集群
复制模板并编辑配置文件：
```bash
cp config/cluster.example.json config/cluster.json
vim config/cluster.json
```
配置示例：
```json
{
  "p": 3,
  "start_time_utc": "2025-12-10 10:00",
  "remote_workdir": "/data/volume-performance-testing",
  "sudo": true,
  "vms": [
    {
      "host": "192.168.1.101",
      "user": "ubuntu",
      "auth": { "type": "key", "value": "~/.ssh/id_rsa" }
    },
    ...
  ]
}
```

### 2. 下发任务
将测试任务分发到所有配置的节点：
```bash
python3 tools/dispatch.py --config config/cluster.json --args "--runtime 60 --cleanup"
```

### 3. 归集结果
待测试完成后，拉取所有节点的报告：
```bash
python3 tools/collect.py --config config/cluster.json
```
结果将保存在 `test_data/reports/centralized/<时间戳>/raw/`。

### 4. 聚合报告
生成集群维度的聚合报告：
```bash
python3 tools/aggregate.py --config config/cluster.json
```
生成 `aggregate.json` 和 `aggregate.md`，汇总所有节点的 IOPS 和带宽。

## 📈 报告对比

本工具提供强大的报告对比功能，用于分析性能变化趋势（例如回归测试或调优前后对比）。支持单机报告和集群聚合报告的对比。

### 1. 自动对比（推荐）
自动对比最近两次的**集群聚合报告**：
```bash
python3 tools/compare.py --auto
```

### 2. 指定版本对比
指定两个时间戳（即 `test_data/reports/centralized/` 下的目录名）进行对比：
```bash
python3 tools/compare.py --baseline 20251210-1000 --current 20251210-1100 --source centralized
```

### 3. 任意目录对比（通用）
对比任意两个包含测试结果的目录（支持单机报告或聚合报告）：
```bash
# 对比两份单机报告
python3 tools/compare.py --dirA test_data/reports/20251210-1000 --dirB test_data/reports/20251210-1100

# 对比两份集群聚合报告
python3 tools/compare.py --dirA test_data/reports/centralized/v1 --dirB test_data/reports/centralized/v2
```

> **输出说明**：对比结果将生成在 `test_data/reports/compare/` 目录下，包含详细的 JSON 数据和易读的 Markdown 报告，展示 IOPS、带宽和延迟的变化量及百分比，并自动标记性能提升 (📈) 或下降 (📉)。

## ⚙️ 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--all` | 运行所有测试 | True |
| `--dd-only` | 仅运行 DD 测试 | False |
| `--fio-only` | 仅运行 FIO 测试 | False |
| `--test-dir` | 测试数据目录 | `./test_data` |
| `--runtime` | FIO 测试时长(秒) | 3 |
| `--quick` | 快速模式 (每项3秒) | False |
| `--cleanup` | 测试后清理文件 | False |
| `--fio-info` | 显示测试矩阵信息 | False |

## 📊 测试指标

- **DD 测试**：
  - 吞吐量 (MB/s)
- **FIO 测试**：
  - IOPS (每秒输入输出次数)
  - 带宽 (MB/s)
  - 延迟 (平均值、P95、P99)

## 📁 项目结构

```
volume-performance-testing/
├── main.py                    # [入口] 主控脚本
├── config_loader.py           # [核心] 配置加载
├── report_generator.py        # [核心] 报告生成
├── core_scenarios_loader.py   # [核心] 场景加载
├── dd_test.py                 # [业务] DD 测试逻辑
├── fio_test.py                # [业务] FIO 测试逻辑
├── models/                    # [模型] 数据类
│   └── result.py
├── utils/                     # [工具] 通用工具
│   ├── logger.py
│   ├── system_info.py
│   └── file_utils.py
├── tools/                     # [辅助] 工具脚本
│   ├── dispatch.py            # 集群任务下发
│   ├── collect.py             # 集群结果归集
│   ├── aggregate.py           # 集群结果聚合
│   ├── compare.py             # 报告对比
│   └── dump_commands.py       # 导出命令清单
└── config/                    # [配置]
    ├── cluster.json           # 集群配置
    └── core_scenarios.json    # 核心场景定义
```

## ❓ 常见问题

**Q: 提示 "fio: command not found"？**
A: 请安装 FIO：`sudo apt-get install fio` (Ubuntu) 或 `sudo yum install fio` (CentOS)。

**Q: 如何自定义核心测试场景？**
A: 修改 `config/core_scenarios.json` 文件。注意：项目仅支持 JSON 格式配置。

**Q: 为什么生成的报告在 test_data 目录下？**
A: 默认情况下，所有测试产生的数据和报告都存储在 `--test-dir` 指定的目录中（默认为 `./test_data`），按时间戳归档，方便管理。

## 📄 许可证

Apache 2.0 License
