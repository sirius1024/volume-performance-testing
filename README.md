# 虚拟机存储性能测试工具

一个全面的虚拟机存储性能测试工具，用于评估和分析存储系统的各项性能指标。

## 📁 项目结构

```
volume-performance-testing/
├── main.py                    # 主控脚本，支持选择测试类型
├── dd_test.py                 # DD测试模块
├── fio_test.py                # FIO测试模块，支持490种配置组合
├── common.py                  # 共享工具类（Logger、SystemInfoCollector等）
├── README.md                  # 项目文档
├── LICENSE                    # 开源许可证
├── .gitignore                 # Git忽略文件配置
└── reports/                   # 测试报告目录（运行时自动创建）
    └── performance_test_report.md  # 测试报告（运行时生成）
```

## 🚀 功能特性

### 核心测试功能
- **DD顺序读写测试** - 使用dd命令测试顺序读写性能
- **FIO随机IO测试** - 490种配置组合的全面随机IO性能测试
  - 7种块大小：4K/8K/16K/32K/64K/1M/4M
  - 7种队列深度：1/2/4/8/16/32/128
  - 智能numjobs映射：根据队列深度自动调整并发数
  - 5种读写比例：100%读/100%写/50%读写/70%读30%写/30%读70%写
- **自定义测试时间** - 支持快速测试（默认3秒）和生产测试（可配置）
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

### 1. 基本使用

```bash
# 运行所有测试（DD + FIO）
python3 main.py

# 仅运行DD测试
python3 main.py --dd-only

# 仅运行FIO测试
python3 main.py --fio-only

# 快速测试模式（部分配置组合）
python3 main.py --quick

# 指定测试目录
python3 main.py --test-dir /tmp/storage_test

# 指定输出报告文件名
python3 main.py --output my_performance_report.md

# 自定义测试时间（生产环境推荐60秒或更长）
python3 main.py --runtime 60

# 测试完成后自动清理测试文件
python3 main.py --cleanup
```

### 2. 独立模块使用

```bash
# 单独运行DD测试
python3 dd_test.py --test-dir /tmp/test --cleanup

# 单独运行FIO测试（420种配置）
python3 fio_test.py --runtime 10 --cleanup

# FIO快速测试模式
python3 fio_test.py --quick --runtime 1 --cleanup

# 查看FIO测试配置信息
python3 fio_test.py --info
```

### 3. 命令行参数说明

#### main.py 主控脚本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--dd-only` | 仅运行DD测试 | `False` |
| `--fio-only` | 仅运行FIO测试 | `False` |
| `--test-dir` | 测试数据目录 | `./test_data` |
| `--output` | 报告输出文件 | `performance_test_report.md` |
| `--cleanup` | 测试完成后清理测试文件 | `False` |
| `--runtime` | 测试时间（秒） | `3` |
| `--quick` | 快速测试模式（仅运行部分配置） | `False` |

#### dd_test.py 独立模块参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--test-dir` | 测试数据目录 | `./test_data` |
| `--cleanup` | 测试完成后清理测试文件 | `False` |

#### fio_test.py 独立模块参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--test-dir` | 测试数据目录 | `./test_data` |
| `--runtime` | FIO测试时间（秒） | `3` |
| `--quick` | 快速测试模式（仅运行部分配置） | `False` |
| `--cleanup` | 测试完成后清理测试文件 | `False` |
| `--info` | 显示测试配置信息 | `False` |

## ⚙️ 配置说明

### FIO测试配置矩阵

脚本支持490种FIO测试配置组合，覆盖以下参数：

#### 块大小 (Block Size)
- 4k, 8k, 16k, 32k, 64k, 1m, 4m（共7种）

#### 队列深度 (iodepth) 和并发数 (numjobs)
- iodepth=1: numjobs=1,4
- iodepth=2: numjobs=1,4  
- iodepth=4: numjobs=1,4
- iodepth=8: numjobs=4,8
- iodepth=16: numjobs=4,8
- iodepth=32: numjobs=8,16
- iodepth=128: numjobs=16,32

#### 读写比例
- 0%读100%写 (randwrite)
- 25%读75%写 (randrw --rwmixread=25)
- 50%读50%写 (randrw --rwmixread=50)
- 75%读25%写 (randrw --rwmixread=75)
- 100%读0%写 (randread)

#### 固定参数
- direct=1 (绕过系统缓存)
- ioengine=libaio (Linux异步IO)
- 测试时间：默认3秒（快速测试），可自定义
- size=1G (测试文件大小)
- time_based (基于时间的测试)
- group_reporting (组合报告)

**总计测试组合**: 7(块大小) × 7(队列深度) × 2(并发数) × 5(读写比例) = 490种配置

### 490种FIO测试场景详细命令

以下是所有490种测试场景的具体FIO命令示例：

#### 基础命令模板
```bash
fio --name=test \
    --filename=fio_test_{block_size}_{queue_depth}_{numjobs}_{rwmix_read} \
    --rw={test_type} \
    --bs={block_size} \
    --iodepth={queue_depth} \
    --numjobs={numjobs} \
    --runtime={runtime} \
    --time_based \
    --direct=1 \
    --ioengine=libaio \
    --group_reporting \
    --output-format=json \
    --size=1G \
    [--rwmixread={rwmix_read}]  # 仅用于randrw类型
```

#### 具体命令示例

**4K块大小测试场景 (70种配置)**
```bash
# 4K + iodepth=1 + numjobs=1 (5种读写比例)
fio --name=test --filename=fio_test_4k_1_1_0 --rw=randwrite --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G
fio --name=test --filename=fio_test_4k_1_1_25 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=25
fio --name=test --filename=fio_test_4k_1_1_50 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=50
fio --name=test --filename=fio_test_4k_1_1_75 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=75
fio --name=test --filename=fio_test_4k_1_1_100 --rw=randread --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G

# 4K + iodepth=1 + numjobs=4 (5种读写比例)
fio --name=test --filename=fio_test_4k_1_4_0 --rw=randwrite --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G
fio --name=test --filename=fio_test_4k_1_4_25 --rw=randrw --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=25
fio --name=test --filename=fio_test_4k_1_4_50 --rw=randrw --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=50
fio --name=test --filename=fio_test_4k_1_4_75 --rw=randrw --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=75
fio --name=test --filename=fio_test_4k_1_4_100 --rw=randread --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G

# 4K + iodepth=2 + numjobs=1,4 (10种配置)
# 4K + iodepth=4 + numjobs=1,4 (10种配置)
# 4K + iodepth=8 + numjobs=4,8 (10种配置)
# 4K + iodepth=16 + numjobs=4,8 (10种配置)
# 4K + iodepth=32 + numjobs=8,16 (10种配置)
# 4K + iodepth=128 + numjobs=16,32 (10种配置)
# ... (其他队列深度配置类似)
```

**8K块大小测试场景 (70种配置)**
```bash
# 8K + 所有队列深度和并发数组合
fio --name=test --filename=fio_test_8k_1_1_0 --rw=randwrite --bs=8k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G
fio --name=test --filename=fio_test_8k_1_1_100 --rw=randread --bs=8k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G
# ... (其他配置类似)
```

**16K块大小测试场景 (70种配置)**
```bash
# 16K + 所有队列深度和并发数组合
fio --name=test --filename=fio_test_16k_32_8_50 --rw=randrw --bs=16k --iodepth=32 --numjobs=8 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=50
# ... (其他配置类似)
```

**32K块大小测试场景 (70种配置)**
```bash
# 32K + 所有队列深度和并发数组合
fio --name=test --filename=fio_test_32k_128_16_75 --rw=randrw --bs=32k --iodepth=128 --numjobs=16 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=75
# ... (其他配置类似)
```

**64K块大小测试场景 (70种配置)**
```bash
# 64K + 所有队列深度和并发数组合
fio --name=test --filename=fio_test_64k_8_8_25 --rw=randrw --bs=64k --iodepth=8 --numjobs=8 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=25
# ... (其他配置类似)
```

**1M块大小测试场景 (70种配置)**
```bash
# 1M + 所有队列深度和并发数组合
fio --name=test --filename=fio_test_1m_16_4_0 --rw=randwrite --bs=1m --iodepth=16 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G
fio --name=test --filename=fio_test_1m_16_8_100 --rw=randread --bs=1m --iodepth=16 --numjobs=8 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G
# ... (其他配置类似)
```

**4M块大小测试场景 (70种配置)**
```bash
# 4M + 所有队列深度和并发数组合
fio --name=test --filename=fio_test_4m_32_16_50 --rw=randrw --bs=4m --iodepth=32 --numjobs=16 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=50
fio --name=test --filename=fio_test_4m_128_32_0 --rw=randwrite --bs=4m --iodepth=128 --numjobs=32 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G
# ... (其他配置类似)
```

#### 参数组合说明

**测试类型映射**:
- rwmix_read=0 → randwrite (100%写)
- rwmix_read=25 → randrw --rwmixread=25 (25%读75%写)
- rwmix_read=50 → randrw --rwmixread=50 (50%读50%写)
- rwmix_read=75 → randrw --rwmixread=75 (75%读25%写)
- rwmix_read=100 → randread (100%读)

**文件名规则**:
- 格式: `fio_test_{block_size}_{queue_depth}_{numjobs}_{rwmix_read}`
- 示例: `fio_test_4k_32_4_50` (4K块大小, 32队列深度, 4并发, 50%读写)

**性能测试目的**:
- **小块大小(4K-16K)**: 模拟数据库、随机访问负载
- **中等块大小(32K-64K)**: 模拟应用程序、文件系统操作
- **大块大小(1M-4M)**: 模拟大文件传输、流媒体、备份操作
- **低队列深度(1-4)**: 模拟单线程应用
- **高队列深度(8-128)**: 模拟高并发、多线程应用
- **不同读写比例**: 模拟各种实际应用场景

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
- **测试矩阵**: 490种配置组合的全面测试
  - **块大小**: 4k, 8k, 16k, 32k, 64k, 1m, 4m（7种）
  - **队列深度**: 1, 2, 4, 8, 16, 32, 128（7种）
  - **并发数**: 每个队列深度支持2种并发配置（2种）
  - **读写比例**: 5种模式覆盖所有典型应用场景
    - 0%读100%写 (randwrite)
    - 25%读75%写 (randrw --rwmixread=25)
    - 50%读50%写 (randrw --rwmixread=50)
    - 75%读25%写 (randrw --rwmixread=75)
    - 100%读0%写 (randread)
- **测试覆盖**: 总计490个测试场景 (7×7×2×5)
- **指标**: IOPS、延迟 (μs)、吞吐量 (MB/s)
- **适用场景**: 数据库、虚拟机磁盘、随机访问负载、性能调优

## 📊 测试报告

测试完成后，会生成详细的Markdown格式报告，包含以下内容：

### 报告结构

1. **测试概述** - 测试时间、环境信息
2. **环境配置** - 系统硬件和软件信息
3. **测试方法** - 使用的测试工具和参数
4. **测试结果** - 详细的性能数据表格
5. **结论与建议** - 性能评估和优化建议

### 报告文件

- 生成 `performance_test_report.md`（或自定义文件名）
- 包含490种FIO测试配置的详细结果
- 按块大小分组展示，便于分析对比

### 报告内容解读

#### 关键性能指标
- **吞吐量 (MB/s)**: 数据传输速率，越高越好
- **IOPS**: 每秒I/O操作数，越高越好
- **延迟 (ms)**: 响应时间，越低越好

#### 性能评估
- **性能等级**: 根据测试结果自动评估（优秀/良好/一般/较差）
- **优化建议**: 针对硬件、软件和监控的具体建议

## 🔧 使用示例

### 示例1: 快速性能测试（推荐）

```bash
# 快速测试模式（部分配置组合，3秒测试时间）
python3 main.py --quick

# 仅运行FIO快速测试
python3 main.py --fio-only --quick

# 测试完成后查看报告
cat performance_test_report.md
```

### 示例2: 完整性能测试

```bash
# 运行完整的490种FIO配置组合测试
python3 main.py --fio-only --runtime 10

# 运行所有测试（DD + FIO）
python3 main.py --runtime 10

# 生产环境完整测试（推荐60秒或更长）
python3 main.py --runtime 60
```

### 示例3: 自定义测试目录和报告

```bash
# 测试特定存储设备并自定义报告名称
python3 main.py \
  --test-dir /mnt/nvme_disk \
  --output nvme_performance_report.md \
  --runtime 30 \
  --cleanup
```

### 示例4: 独立模块测试

```bash
# 单独运行DD测试
python3 dd_test.py --test-dir /tmp/test --cleanup

# 单独运行FIO测试并查看配置信息
python3 fio_test.py --info
python3 fio_test.py --runtime 10 --cleanup
```

### 示例5: 批量测试不同存储设备

```bash
#!/bin/bash
# 测试多个存储设备
for device in "/mnt/ssd" "/mnt/hdd" "/tmp"; do
  echo "Testing $device..."
  python3 main.py \
    --test-dir "$device/storage_test" \
    --output "$(basename $device)_performance_report.md" \
    --cleanup
done
```

### 示例6: 不同测试时间对比

```bash
# 快速冒烟测试（3秒）
python3 main.py --quick --output quick_test.md
```bash
# 标准测试（10秒）
python3 main.py --runtime 10 --output standard_test.md

# 生产级测试（60秒）
python3 main.py --runtime 60 --output production_test.md
```

## ❓ 常见问题

### Q1: 测试失败，提示"fio command not found"
**A**: 需要安装fio工具
```bash
sudo apt-get install fio  # Ubuntu/Debian
sudo yum install fio      # CentOS/RHEL
```

### Q2: 如何选择合适的测试模式？
**A**: 
- **快速评估**: 使用 `--quick` 参数进行快速测试
- **标准测试**: 使用 `--fio-runtime 10` 进行10秒测试
- **生产级测试**: 使用 `--fio-runtime 60` 或更长时间
- **特定场景**: 根据实际应用需求调整测试时间

### Q3: 测试结果如何解读？
**A**: 
- **IOPS**: 越高越好，关注随机读写性能
- **延迟**: 越低越好，特别是P99延迟
- **吞吐量**: 顺序读写的重要指标
- **490种配置**: 可按块大小、队列深度、读写比例分析性能特征

### Q4: 可以在生产环境运行吗？
**A**: 
- **快速模式**: 相对安全，但建议在维护窗口运行
- **完整测试**: 包含大量写入测试，可能影响性能，谨慎使用
- **建议**: 先在测试环境验证，确认无误后再用于生产

### Q5: 如何优化测试性能？
**A**: 
- 使用SSD存储运行测试脚本
- 确保测试目录在被测存储设备上
- 关闭不必要的系统服务
- 使用专用的测试环境
- 根据存储类型选择合适的测试时间

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

## 🏗️ 架构设计

### 模块化架构

项目采用模块化设计，将DD测试和FIO测试分离管理：

- **main.py**: 主控脚本，提供统一的命令行接口
- **dd_test.py**: DD测试模块，专门处理顺序读写测试
- **fio_test.py**: FIO测试模块，处理420种随机IO测试配置
- **common.py**: 共享工具类，包含日志、系统信息收集、报告生成等

### 优势

1. **模块独立**: 每个测试模块可以独立运行和维护
2. **代码复用**: 共享工具类避免代码重复
3. **易于扩展**: 可以轻松添加新的测试模块
4. **灵活使用**: 支持选择性运行特定测试类型

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

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您在使用过程中遇到问题，请：
1. 查看本文档的故障排除部分
2. 搜索已有的Issues
3. 创建新的Issue并提供详细信息

---

**Happy Testing! 🚀**