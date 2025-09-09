# 虚拟机存储性能测试报告

## 测试概述

**测试日期：** [填写测试日期]
**测试人员：** [填写测试人员]
**报告版本：** [填写版本号]

---

## 1. 测试环境配置

### 1.1 虚拟机规格

| 配置项 | 规格 | 备注 |
|--------|------|------|
| CPU | [填写CPU型号和核数] | 例：Intel Xeon E5-2680 v4 @ 2.40GHz, 8核 |
| 内存 | [填写内存大小] | 例：16GB DDR4 |
| 操作系统 | [填写操作系统版本] | 例：Ubuntu 22.04.3 LTS |
| 内核版本 | [填写内核版本] | 例：Linux 5.15.0-78-generic |
| 存储类型 | [填写存储类型] | 例：SSD/HDD/NVMe |
| 文件系统 | [填写文件系统] | 例：ext4/xfs/btrfs |
| 磁盘容量 | [填写磁盘容量] | 例：500GB |

### 1.2 测试工具版本

| 工具 | 版本 | 用途 |
|------|------|------|
| dd | [填写版本] | 顺序读写性能测试 |
| fio | [填写版本] | 随机IO性能测试 |
| Python | [填写版本] | 测试脚本执行环境 |

### 1.3 测试环境准备

- **测试目录：** [填写测试目录路径]
- **可用空间：** [填写可用磁盘空间]
- **系统负载：** [填写测试时系统负载情况]
- **网络状态：** [填写网络连接状态]

---

## 2. 测试方法

### 2.1 DD命令顺序读写测试

#### 2.1.1 顺序写入测试

**测试命令：**
```bash
# 1GB文件写入测试
dd if=/dev/zero of=testfile_1g bs=1G count=1 oflag=direct

# 4GB文件写入测试
dd if=/dev/zero of=testfile_4g bs=1G count=4 oflag=direct

# 不同块大小写入测试
dd if=/dev/zero of=testfile_1m bs=1M count=1024 oflag=direct
dd if=/dev/zero of=testfile_4k bs=4K count=262144 oflag=direct
```

**参数说明：**
- `if=/dev/zero`：输入源为零设备
- `of=testfile`：输出文件名
- `bs`：块大小（1G/1M/4K等）
- `count`：块数量
- `oflag=direct`：绕过系统缓存，直接IO

#### 2.1.2 顺序读取测试

**测试命令：**
```bash
# 清除系统缓存
echo 3 > /proc/sys/vm/drop_caches

# 1GB文件读取测试
dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct

# 4GB文件读取测试
dd if=testfile_4g of=/dev/null bs=1G count=4 iflag=direct

# 不同块大小读取测试
dd if=testfile_1m of=/dev/null bs=1M count=1024 iflag=direct
dd if=testfile_4k of=/dev/null bs=4K count=262144 iflag=direct
```

**参数说明：**
- `if=testfile`：输入文件名
- `of=/dev/null`：输出到空设备
- `iflag=direct`：绕过系统缓存，直接IO

### 2.2 FIO命令随机IO测试

#### 2.2.1 随机读写性能测试

**4K随机读测试：**
```bash
fio --name=4k_random_read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting
```

**4K随机写测试：**
```bash
fio --name=4k_random_write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting
```

**不同块大小随机读写测试：**
```bash
# 8K随机读写
fio --name=8k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=8k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 16K随机读写
fio --name=16k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=16k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 64K随机读写
fio --name=64k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=64k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 1M随机读写
fio --name=1m_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=1m --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 4M随机读写
fio --name=4m_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4m --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting
```

#### 2.2.2 队列深度测试

**不同队列深度4K随机读测试：**
```bash
# 队列深度1
fio --name=4k_qd1 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=1 --numjobs=1 --runtime=60 --group_reporting

# 队列深度4
fio --name=4k_qd4 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=4 --numjobs=1 --runtime=60 --group_reporting

# 队列深度8
fio --name=4k_qd8 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=8 --numjobs=1 --runtime=60 --group_reporting

# 队列深度16
fio --name=4k_qd16 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=16 --numjobs=1 --runtime=60 --group_reporting

# 队列深度32
fio --name=4k_qd32 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=32 --numjobs=1 --runtime=60 --group_reporting
```

#### 2.2.3 混合读写比例测试

**不同读写比例测试：**
```bash
# 100%读
fio --name=100read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 70%读30%写
fio --name=70read_30write --ioengine=libaio --rw=randrw --rwmixread=70 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 50%读50%写
fio --name=50read_50write --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 30%读70%写
fio --name=30read_70write --ioengine=libaio --rw=randrw --rwmixread=30 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 100%写
fio --name=100write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting
```

#### 2.2.4 并发测试

**不同并发数测试：**
```bash
# 1个并发
fio --name=1job --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting

# 2个并发
fio --name=2jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=2 --runtime=60 --group_reporting

# 4个并发
fio --name=4jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=4 --runtime=60 --group_reporting

# 8个并发
fio --name=8jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=8 --runtime=60 --group_reporting

# 16个并发
fio --name=16jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=16 --runtime=60 --group_reporting

# 32个并发
fio --name=32jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=32 --runtime=60 --group_reporting
```

**FIO参数说明：**
- `--name`：测试任务名称
- `--ioengine`：IO引擎（libaio/sync/psync等）
- `--rw`：读写模式（read/write/randread/randwrite/randrw等）
- `--bs`：块大小
- `--direct`：是否使用直接IO（1=是，0=否）
- `--size`：测试文件大小
- `--numjobs`：并发任务数
- `--iodepth`：队列深度
- `--runtime`：运行时间（秒）
- `--rwmixread`：混合读写中读的比例
- `--group_reporting`：汇总报告

---

## 3. 测试结果

### 3.1 DD命令顺序读写测试结果

#### 3.1.1 顺序写入性能

| 块大小 | 文件大小 | 写入速度 | 耗时 | 命令 |
|--------|----------|----------|------|------|
| 1G | 1GB | [填写速度] MB/s | [填写时间] s | `dd if=/dev/zero of=testfile_1g bs=1G count=1 oflag=direct` |
| 1G | 4GB | [填写速度] MB/s | [填写时间] s | `dd if=/dev/zero of=testfile_4g bs=1G count=4 oflag=direct` |
| 1M | 1GB | [填写速度] MB/s | [填写时间] s | `dd if=/dev/zero of=testfile_1m bs=1M count=1024 oflag=direct` |
| 4K | 1GB | [填写速度] MB/s | [填写时间] s | `dd if=/dev/zero of=testfile_4k bs=4K count=262144 oflag=direct` |

#### 3.1.2 顺序读取性能

| 块大小 | 文件大小 | 读取速度 | 耗时 | 命令 |
|--------|----------|----------|------|------|
| 1G | 1GB | [填写速度] MB/s | [填写时间] s | `dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct` |
| 1G | 4GB | [填写速度] MB/s | [填写时间] s | `dd if=testfile_4g of=/dev/null bs=1G count=4 iflag=direct` |
| 1M | 1GB | [填写速度] MB/s | [填写时间] s | `dd if=testfile_1m of=/dev/null bs=1M count=1024 iflag=direct` |
| 4K | 1GB | [填写速度] MB/s | [填写时间] s | `dd if=testfile_4k of=/dev/null bs=4K count=262144 iflag=direct` |

### 3.2 FIO随机IO测试结果

#### 3.2.1 不同块大小随机读写性能

| 块大小 | 读写模式 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|--------|----------|------|------------|--------------|-------------|------|
| 4K | 随机读 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4k_random_read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 4K | 随机写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4k_random_write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 8K | 随机读写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=8k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=8k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 16K | 随机读写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=16k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=16k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 64K | 随机读写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=64k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=64k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 1M | 随机读写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=1m_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=1m --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 4M | 随机读写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4m_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4m --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |

#### 3.2.2 队列深度对性能的影响

| 队列深度 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|----------|------|------------|--------------|-------------|------|
| 1 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4k_qd1 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=1 --numjobs=1 --runtime=60 --group_reporting` |
| 4 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4k_qd4 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=4 --numjobs=1 --runtime=60 --group_reporting` |
| 8 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4k_qd8 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=8 --numjobs=1 --runtime=60 --group_reporting` |
| 16 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4k_qd16 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=16 --numjobs=1 --runtime=60 --group_reporting` |
| 32 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4k_qd32 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=32 --numjobs=1 --runtime=60 --group_reporting` |

#### 3.2.3 混合读写比例测试结果

| 读写比例 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|----------|------|------------|--------------|-------------|------|
| 100%读 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=100read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 70%读30%写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=70read_30write --ioengine=libaio --rw=randrw --rwmixread=70 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 50%读50%写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=50read_50write --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 30%读70%写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=30read_70write --ioengine=libaio --rw=randrw --rwmixread=30 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 100%写 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=100write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |

#### 3.2.4 并发测试结果

| 并发数 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|--------|------|------------|--------------|-------------|------|
| 1 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=1job --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 2 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=2jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=2 --runtime=60 --group_reporting` |
| 4 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=4jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=4 --runtime=60 --group_reporting` |
| 8 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=8jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=8 --runtime=60 --group_reporting` |
| 16 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=16jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=16 --runtime=60 --group_reporting` |
| 32 | [填写IOPS] | [填写带宽] | [填写延迟] | [填写延迟] | `fio --name=32jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=32 --runtime=60 --group_reporting` |

### 3.3 关键性能指标汇总

| 测试类型 | 最佳性能 | 平均性能 | 最差性能 | 性能波动率 |
|----------|----------|----------|----------|------------|
| 顺序读取速度 | [填写数值] MB/s | [填写数值] MB/s | [填写数值] MB/s | [填写百分比]% |
| 顺序写入速度 | [填写数值] MB/s | [填写数值] MB/s | [填写数值] MB/s | [填写百分比]% |
| 4K随机读IOPS | [填写数值] | [填写数值] | [填写数值] | [填写百分比]% |
| 4K随机写IOPS | [填写数值] | [填写数值] | [填写数值] | [填写百分比]% |
| 平均延迟 | [填写数值] μs | [填写数值] μs | [填写数值] μs | [填写百分比]% |
| 99%延迟 | [填写数值] μs | [填写数值] μs | [填写数值] μs | [填写百分比]% |

### 3.4 性能波动分析

#### 3.4.1 测试过程中的性能变化

**观察到的性能波动现象：**
- [填写观察到的性能波动情况]
- [填写可能的波动原因分析]
- [填写波动对业务的潜在影响]

#### 3.4.2 多次测试结果对比

| 测试轮次 | 4K随机读IOPS | 4K随机写IOPS | 顺序读(MB/s) | 顺序写(MB/s) |
|----------|--------------|--------------|--------------|-------------|
| 第1次 | [填写数值] | [填写数值] | [填写数值] | [填写数值] |
| 第2次 | [填写数值] | [填写数值] | [填写数值] | [填写数值] |
| 第3次 | [填写数值] | [填写数值] | [填写数值] | [填写数值] |
| 平均值 | [填写数值] | [填写数值] | [填写数值] | [填写数值] |
| 标准差 | [填写数值] | [填写数值] | [填写数值] | [填写数值] |
| 变异系数 | [填写百分比]% | [填写百分比]% | [填写百分比]% | [填写百分比]% |

---

## 4. 结论与建议

### 4.1 存储性能评估

#### 4.1.1 整体性能水平

**顺序读写性能：**
- 顺序读取速度：[填写评估结果]
- 顺序写入速度：[填写评估结果]
- 性能等级：[优秀/良好/一般/较差]

**随机IO性能：**
- 4K随机读IOPS：[填写评估结果]
- 4K随机写IOPS：[填写评估结果]
- 延迟表现：[填写评估结果]
- 性能等级：[优秀/良好/一般/较差]

#### 4.1.2 性能特点分析

**优势：**
- [填写存储系统的性能优势]
- [填写适合的应用场景]

**劣势：**
- [填写存储系统的性能劣势]
- [填写需要注意的限制]

### 4.2 业务适用性分析

#### 4.2.1 适合运行的业务类型

**数据库应用：**
- **OLTP数据库**：[根据4K随机读写IOPS和延迟评估适用性]
- **OLAP数据库**：[根据顺序读写性能评估适用性]
- **NoSQL数据库**：[根据混合读写性能评估适用性]

**Web应用：**
- **高并发Web系统**：[根据并发测试结果评估适用性]
- **内容管理系统**：[根据文件读写性能评估适用性]
- **电商平台**：[根据混合负载性能评估适用性]

**流媒体应用：**
- **视频点播**：[根据顺序读性能评估适用性]
- **直播系统**：[根据写入性能和延迟评估适用性]
- **音频处理**：[根据小文件性能评估适用性]

**大数据应用：**
- **数据仓库**：[根据大块顺序读写性能评估适用性]
- **日志分析**：[根据写入性能评估适用性]
- **机器学习**：[根据随机读性能评估适用性]

**虚拟化应用：**
- **虚拟机存储**：[根据混合负载性能评估适用性]
- **容器存储**：[根据小文件性能评估适用性]

#### 4.2.2 不适合的业务场景

- [填写不适合的业务类型及原因]
- [填写性能限制可能导致的问题]

### 4.3 潜在瓶颈分析

#### 4.3.1 性能瓶颈识别

**IOPS瓶颈：**
- 当前4K随机读IOPS：[填写数值]
- 当前4K随机写IOPS：[填写数值]
- 瓶颈分析：[填写是否存在IOPS瓶颈]

**带宽瓶颈：**
- 当前顺序读带宽：[填写数值] MB/s
- 当前顺序写带宽：[填写数值] MB/s
- 瓶颈分析：[填写是否存在带宽瓶颈]

**延迟瓶颈：**
- 当前平均延迟：[填写数值] μs
- 当前99%延迟：[填写数值] μs
- 瓶颈分析：[填写是否存在延迟瓶颈]

#### 4.3.2 瓶颈成因分析

**硬件层面：**
- [填写可能的硬件瓶颈]
- [填写存储介质限制]

**软件层面：**
- [填写可能的软件瓶颈]
- [填写配置优化空间]

**系统层面：**
- [填写可能的系统瓶颈]
- [填写资源竞争情况]

### 4.4 优化建议

#### 4.4.1 硬件优化建议

**存储硬件：**
- [填写存储硬件升级建议]
- [填写RAID配置优化建议]

**系统硬件：**
- [填写CPU/内存优化建议]
- [填写网络优化建议]

#### 4.4.2 软件优化建议

**操作系统优化：**
- [填写内核参数调优建议]
- [填写文件系统优化建议]

**应用层优化：**
- [填写应用配置优化建议]
- [填写缓存策略优化建议]

#### 4.4.3 配置优化建议

**IO调度器：**
- 当前调度器：[填写当前调度器]
- 推荐调度器：[填写推荐调度器]
- 优化命令：`echo [调度器] > /sys/block/[设备]/queue/scheduler`

**文件系统参数：**
- [填写文件系统挂载参数优化建议]
- [填写文件系统特定优化建议]

**系统参数：**
- [填写/proc/sys参数优化建议]
- [填写ulimit参数优化建议]

### 4.5 监控建议

#### 4.5.1 关键指标监控

**实时监控指标：**
- IOPS（读/写）
- 带宽（读/写）
- 延迟（平均/99%）
- 队列深度
- CPU使用率
- 内存使用率

**监控工具推荐：**
- `iostat -x 1`：实时IO统计
- `iotop`：进程IO监控
- `dstat`：系统资源监控
- `fio --output-format=json`：详细性能测试

#### 4.5.2 告警阈值建议

| 指标 | 警告阈值 | 严重阈值 | 说明 |
|------|----------|----------|------|
| IOPS使用率 | 80% | 90% | 相对于测试最大值 |
| 带宽使用率 | 80% | 90% | 相对于测试最大值 |
| 平均延迟 | [填写阈值] μs | [填写阈值] μs | 根据业务需求设定 |
| 99%延迟 | [填写阈值] μs | [填写阈值] μs | 根据业务需求设定 |
| 队列深度 | [填写阈值] | [填写阈值] | 避免过度排队 |

---

## 5. 附录

### 5.1 原始测试数据

#### 5.1.1 DD命令原始输出

**顺序写入测试原始数据：**
```
[粘贴dd命令的完整输出]
```

**顺序读取测试原始数据：**
```
[粘贴dd命令的完整输出]
```

#### 5.1.2 FIO命令原始输出

**4K随机读测试原始数据：**
```
[粘贴fio命令的完整JSON输出]
```

**4K随机写测试原始数据：**
```
[粘贴fio命令的完整JSON输出]
```

**队列深度测试原始数据：**
```
[粘贴各队列深度测试的完整输出]
```

**并发测试原始数据：**
```
[粘贴各并发数测试的完整输出]
```

### 5.2 测试脚本

#### 5.2.1 自动化测试脚本

```bash
#!/bin/bash
# 虚拟机存储性能自动化测试脚本

# 测试配置
TEST_DIR="/tmp/storage_test"
TEST_SIZE="1G"
RUNTIME="60"

# 创建测试目录
mkdir -p $TEST_DIR
cd $TEST_DIR

# DD顺序测试
echo "开始DD顺序测试..."
dd if=/dev/zero of=testfile_1g bs=1G count=1 oflag=direct
echo 3 > /proc/sys/vm/drop_caches
dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct

# FIO随机测试
echo "开始FIO随机测试..."
fio --name=4k_random_read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=$TEST_SIZE --numjobs=1 --runtime=$RUNTIME --group_reporting --output-format=json > 4k_read.json
fio --name=4k_random_write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=$TEST_SIZE --numjobs=1 --runtime=$RUNTIME --group_reporting --output-format=json > 4k_write.json

# 清理测试文件
rm -f testfile_*
echo "测试完成！"
```

### 5.3 性能基准参考

#### 5.3.1 不同存储类型性能基准

| 存储类型 | 顺序读(MB/s) | 顺序写(MB/s) | 4K随机读IOPS | 4K随机写IOPS | 延迟(μs) |
|----------|--------------|--------------|--------------|--------------|----------|
| SATA SSD | 500-550 | 450-500 | 80K-100K | 70K-90K | 50-100 |
| NVMe SSD | 3000-7000 | 2000-6000 | 300K-1M | 200K-800K | 10-50 |
| SATA HDD | 100-200 | 100-180 | 100-200 | 100-150 | 5000-15000 |
| SAS HDD | 150-250 | 150-220 | 200-400 | 150-300 | 3000-10000 |

#### 5.3.2 业务场景性能要求

| 业务场景 | IOPS要求 | 延迟要求 | 带宽要求 |
|----------|----------|----------|----------|
| OLTP数据库 | >10K | <1ms | >100MB/s |
| OLAP数据库 | >1K | <10ms | >500MB/s |
| Web应用 | >5K | <5ms | >200MB/s |
| 流媒体 | >1K | <100ms | >1GB/s |
| 文件服务 | >2K | <10ms | >300MB/s |

---

**报告生成时间：** [自动填写]
**测试工具版本：** [自动填写]
**报告版本：** v1.0