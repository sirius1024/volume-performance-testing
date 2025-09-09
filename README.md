# 虚拟机存储性能测试工具

一个全面的虚拟机存储性能测试工具，用于评估和分析存储系统的各项性能指标。本项目提供两个版本的测试脚本：

- `vm_storage_performance_test.py` - 原始版本，功能完整
- `enhanced_vm_storage_test.py` - 增强版本，更简洁高效（推荐使用）

## 🚀 功能特性

### 核心测试功能
- **DD顺序读写测试** - 使用dd命令测试顺序读写性能
- **FIO随机IO测试** - 多种块大小的随机读写性能测试
- **队列深度测试** - 测试不同队列深度对性能的影响
- **混合读写比例测试** - 测试不同读写比例下的性能表现
- **并发测试** - 多任务并发访问性能测试
- **系统信息收集** - 自动收集CPU、内存、存储等系统信息
- **智能报告生成** - 生成详细的Markdown格式测试报告

## 📋 系统要求

### 必需依赖
- Python 3.6+
- fio (Flexible I/O Tester)
- 足够的磁盘空间用于测试文件（建议至少2GB空闲空间）

### 安装依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install fio python3 python3-pip

# CentOS/RHEL
sudo yum install fio python3 python3-pip

# 或使用dnf (较新版本)
sudo dnf install fio python3 python3-pip

# macOS (使用Homebrew)
brew install fio python3
```

## 🏃 快速开始

### 1. 增强版脚本使用（推荐）

```bash
# 使用默认配置运行所有测试
python3 enhanced_vm_storage_test.py

# 指定测试目录
python3 enhanced_vm_storage_test.py --test-dir /tmp/storage_test

# 指定输出报告文件名
python3 enhanced_vm_storage_test.py --output my_performance_report.md

# 测试完成后自动清理测试文件
python3 enhanced_vm_storage_test.py --cleanup
```

### 2. 原始版本使用

```bash
# 使用默认配置运行所有测试
python3 vm_storage_performance_test.py

# 使用配置文件
python3 vm_storage_performance_test.py --config config.json

# 快速测试
python3 vm_storage_performance_test.py --config quick_test_config.json
```

### 3. 命令行参数说明

#### enhanced_vm_storage_test.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--test-dir` | 测试数据目录 | `./test_data` |
| `--output` | 报告输出文件 | `performance_test_report.md` |
| `--cleanup` | 测试完成后清理测试文件 | `False` |

#### vm_storage_performance_test.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config` | 配置文件路径 | `config.json` |
| `--test-dir` | 测试数据目录 | `./test_data` |
| `--runtime` | 测试运行时间（秒） | `60` |

## ⚙️ 配置说明

### 增强版脚本 (enhanced_vm_storage_test.py)

增强版脚本使用内置的优化配置，无需额外配置文件：
- **测试文件大小**: 自动根据测试类型调整（1M-1G）
- **测试时间**: 每个测试约10-30秒
- **测试覆盖**: 包含所有主要性能指标
- **自动优化**: 根据系统资源自动调整参数

### 原始版脚本配置文件

原始版本支持详细的配置文件定制，适合高级用户：
- `config.json` - 完整测试配置
- `quick_test_config.json` - 快速测试配置

详细配置参数请参考配置文件中的注释说明。

## 🧪 测试类型详解

### 1. DD顺序读写测试
- **目的**: 使用dd命令评估顺序读写性能
- **测试项**: 
  - 顺序写入测试（1M、4K、1G块大小）
  - 顺序读取测试（1M、4K、1G块大小）
- **指标**: 吞吐量 (MB/s)
- **适用场景**: 大文件传输、数据备份、流媒体

### 2. FIO随机IO测试
- **目的**: 评估随机I/O性能
- **测试项**:
  - 4K随机读取
  - 4K随机写入
  - 4K随机读写混合
  - 多种块大小测试（16K、64K、1M、4M）
- **指标**: IOPS、延迟 (ms)、吞吐量 (MB/s)
- **适用场景**: 数据库、虚拟机磁盘、随机访问负载

### 3. 队列深度测试
- **目的**: 测试不同队列深度对性能的影响
- **测试项**: QD=1, 4, 8, 16, 32
- **指标**: IOPS、延迟随队列深度的变化
- **适用场景**: 优化存储配置和应用程序参数

### 4. 混合读写比例测试
- **目的**: 测试不同读写比例下的性能表现
- **测试项**: 
  - 100%读取
  - 70%读取 + 30%写入
  - 50%读取 + 50%写入
  - 30%读取 + 70%写入
  - 100%写入
- **指标**: 混合负载下的IOPS和延迟
- **适用场景**: 真实应用负载模拟

### 5. 并发测试
- **目的**: 测试多任务并发访问性能
- **测试项**: 1, 2, 4, 8, 16, 32个并发任务
- **指标**: 总IOPS、平均延迟、扩展性
- **适用场景**: 多用户、多应用并发访问

## 📊 测试报告

测试完成后，会生成详细的Markdown格式报告，包含以下内容：

### 报告结构

1. **测试概述** - 测试时间、环境信息
2. **环境配置** - 系统硬件和软件信息
3. **测试方法** - 使用的测试工具和参数
4. **测试结果** - 详细的性能数据表格
5. **结论与建议** - 性能评估和优化建议

### 报告文件

- **增强版脚本**: 生成 `performance_test_report.md`（或自定义文件名）
- **原始版脚本**: 生成多种格式报告（HTML、JSON、CSV）

### 报告内容解读

#### 关键性能指标
- **吞吐量 (MB/s)**: 数据传输速率，越高越好
- **IOPS**: 每秒I/O操作数，越高越好
- **延迟 (ms)**: 响应时间，越低越好

#### 性能评估
- **性能等级**: 根据测试结果自动评估（优秀/良好/一般/较差）
- **优化建议**: 针对硬件、软件和监控的具体建议

## 🔧 使用示例

### 示例1: 基础性能测试（推荐）

```bash
# 使用增强版脚本进行基础测试
python3 enhanced_vm_storage_test.py

# 测试完成后查看报告
cat performance_test_report.md
```

### 示例2: 自定义测试目录和报告

```bash
# 测试特定存储设备并自定义报告名称
python3 enhanced_vm_storage_test.py \
  --test-dir /mnt/nvme_disk \
  --output nvme_performance_report.md \
  --cleanup
```

### 示例3: 完整功能测试（原始版本）

```bash
# 使用原始版本进行完整测试
python3 vm_storage_performance_test.py --config config.json

# 快速测试
python3 vm_storage_performance_test.py --config quick_test_config.json
```

### 示例4: 批量测试不同存储设备

```bash
#!/bin/bash
# 测试多个存储设备
for device in "/mnt/ssd" "/mnt/hdd" "/tmp"; do
  echo "Testing $device..."
  python3 enhanced_vm_storage_test.py \
    --test-dir "$device/storage_test" \
    --output "$(basename $device)_performance_report.md" \
    --cleanup
done
```

### 示例4: 创建自定义配置

```bash
# 复制并修改配置文件
cp config.json my_config.json
# 编辑 my_config.json 调整测试参数
python3 vm_storage_performance_test.py --config my_config.json
```

## ❓ 常见问题

### Q1: 测试失败，提示"fio command not found"
**A**: 需要安装fio工具
```bash
sudo apt-get install fio  # Ubuntu/Debian
sudo yum install fio      # CentOS/RHEL
```

### Q2: 测试过程中磁盘空间不足
**A**: 
- 减小 `test_file_size` 参数
- 选择有足够空间的测试目录
- 使用 `quick_test_config.json` 进行轻量测试

### Q3: 测试时间过长
**A**: 
- 减少 `runtime` 参数
- 减少测试参数组合数量
- 使用快速测试配置

### Q4: 权限不足无法创建测试文件
**A**: 
- 确保对测试目录有写权限
- 使用 `sudo` 运行（不推荐）
- 更改测试目录到用户有权限的位置

### Q5: 如何解读性能测试结果？
**A**: 
- 关注IOPS和延迟指标
- 查看HTML报告中的性能瓶颈分析
- 对比不同配置下的测试结果
- 参考优化建议进行系统调优

## 🎯 性能优化建议

### 存储层面
1. **使用SSD替代HDD**: 显著提升随机I/O性能
2. **启用写缓存**: 提高写入性能（注意数据安全）
3. **调整I/O调度器**: 根据负载类型选择合适的调度器
4. **优化文件系统**: 选择适合的文件系统和挂载参数

### 系统层面
1. **增加内存**: 提高文件系统缓存效果
2. **调整内核参数**: 优化I/O相关的内核参数
3. **CPU亲和性**: 绑定I/O密集进程到特定CPU核心
4. **网络优化**: 对于网络存储，优化网络配置

### 应用层面
1. **合理设置队列深度**: 根据存储类型调整
2. **选择合适的块大小**: 平衡吞吐量和延迟
3. **使用异步I/O**: 提高并发性能
4. **批量操作**: 减少I/O操作次数

## 📝 日志和调试

测试过程中会生成详细日志文件 `vm_storage_test.log`，包含：
- 测试执行过程
- 错误信息和警告
- 性能数据采集详情
- 系统资源使用情况

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个工具！



## ⚠️ 注意事项

### 测试前准备
1. **确保足够的磁盘空间**: 测试会创建临时文件，建议至少2GB空闲空间
2. **关闭不必要的程序**: 避免其他程序影响测试结果
3. **检查权限**: 确保对测试目录有读写权限
4. **备份重要数据**: 虽然测试不会影响现有数据，但建议提前备份

### 测试期间
- 测试过程中会产生大量磁盘I/O，可能影响系统响应速度
- 建议在系统空闲时进行测试
- 不要在测试过程中进行其他磁盘密集型操作

### 测试结果解读
- **IOPS**: 数值越高表示随机访问性能越好
- **吞吐量**: 数值越高表示顺序访问性能越好
- **延迟**: 数值越低表示响应速度越快
- 不同存储类型的性能差异很大，建议与同类产品对比

## 🔧 故障排除

### 常见问题

**Q: 提示"fio: command not found"**
```bash
# 安装fio工具
sudo apt-get install fio  # Ubuntu/Debian
sudo yum install fio      # CentOS/RHEL
```

**Q: 权限被拒绝错误**
```bash
# 检查测试目录权限
ls -la ./test_data
# 修改权限
chmod 755 ./test_data
```

**Q: 磁盘空间不足**
```bash
# 检查可用空间
df -h .
# 清理测试文件
python3 enhanced_vm_storage_test.py --cleanup
```

**Q: 测试时间过长**
- 使用原始版本的快速配置: `--config quick_test_config.json`
- 增强版本默认已经优化了测试时间

## 📁 项目结构

```
volume-performance-testing/
├── enhanced_vm_storage_test.py    # 增强版测试脚本（推荐）
├── vm_storage_performance_test.py # 原始版测试脚本
├── config.json                    # 原始版配置文件
├── quick_test_config.json         # 快速测试配置
├── performance_test_report_template.md  # 报告模板
├── test_data/                     # 测试数据目录
├── *.log                         # 测试日志文件
├── *_report.md                   # 生成的测试报告
├── LICENSE                       # 开源许可证
└── README.md                     # 项目说明文档
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 开发环境设置
```bash
git clone <repository-url>
cd volume-performance-testing
# 安装依赖
sudo apt-get install fio python3
```

### 提交规范
- 提交前请确保代码通过测试
- 遵循现有的代码风格
- 提供清晰的提交信息

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您在使用过程中遇到问题，请：
1. 查看本文档的故障排除部分
2. 搜索已有的Issues
3. 创建新的Issue并提供详细信息

---

**Happy Testing! 🚀**