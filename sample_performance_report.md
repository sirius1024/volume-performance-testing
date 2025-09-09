# 虚拟机存储性能测试报告 - 示例

## 测试概述

**测试日期：** 2024-01-15
**测试人员：** 系统管理员
**报告版本：** v1.0

---

## 1. 测试环境配置

### 1.1 虚拟机规格

| 配置项 | 规格 | 备注 |
|--------|------|------|
| CPU | Intel Xeon E5-2680 v4 @ 2.40GHz, 8核 | 虚拟化环境 |
| 内存 | 16GB DDR4 | 2400MHz |
| 操作系统 | Ubuntu 22.04.3 LTS | 64位 |
| 内核版本 | Linux 5.15.0-78-generic | 默认内核 |
| 存储类型 | NVMe SSD | 企业级 |
| 文件系统 | ext4 | 默认配置 |
| 磁盘容量 | 500GB | 可用空间450GB |

### 1.2 测试工具版本

| 工具 | 版本 | 用途 |
|------|------|------|
| dd | 8.32 | 顺序读写性能测试 |
| fio | 3.36 | 随机IO性能测试 |
| Python | 3.12.3 | 测试脚本执行环境 |

### 1.3 测试环境准备

- **测试目录：** /tmp/storage_test
- **可用空间：** 450GB
- **系统负载：** 空闲状态，CPU使用率<5%
- **网络状态：** 本地测试，无网络IO影响

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

#### 2.1.2 顺序读取测试

**测试命令：**
```bash
# 清除系统缓存
echo 3 > /proc/sys/vm/drop_caches

# 读取测试
dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct
dd if=testfile_4g of=/dev/null bs=1G count=4 iflag=direct
dd if=testfile_1m of=/dev/null bs=1M count=1024 iflag=direct
dd if=testfile_4k of=/dev/null bs=4K count=262144 iflag=direct
```

### 2.2 FIO命令随机IO测试

#### 2.2.1 基础随机读写测试

**4K随机读测试：**
```bash
fio --name=4k_random_read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting
```

**4K随机写测试：**
```bash
fio --name=4k_random_write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting
```

---

## 3. 测试结果

### 3.1 DD命令顺序读写测试结果

#### 3.1.1 顺序写入性能

| 块大小 | 文件大小 | 写入速度 | 耗时 | 命令 |
|--------|----------|----------|------|------|
| 1G | 1GB | 2850 MB/s | 0.36 s | `dd if=/dev/zero of=testfile_1g bs=1G count=1 oflag=direct` |
| 1G | 4GB | 2720 MB/s | 1.47 s | `dd if=/dev/zero of=testfile_4g bs=1G count=4 oflag=direct` |
| 1M | 1GB | 2650 MB/s | 0.39 s | `dd if=/dev/zero of=testfile_1m bs=1M count=1024 oflag=direct` |
| 4K | 1GB | 1850 MB/s | 0.55 s | `dd if=/dev/zero of=testfile_4k bs=4K count=262144 oflag=direct` |

#### 3.1.2 顺序读取性能

| 块大小 | 文件大小 | 读取速度 | 耗时 | 命令 |
|--------|----------|----------|----------|------|
| 1G | 1GB | 3200 MB/s | 0.32 s | `dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct` |
| 1G | 4GB | 3150 MB/s | 1.27 s | `dd if=testfile_4g of=/dev/null bs=1G count=4 iflag=direct` |
| 1M | 1GB | 3100 MB/s | 0.33 s | `dd if=testfile_1m of=/dev/null bs=1M count=1024 iflag=direct` |
| 4K | 1GB | 2200 MB/s | 0.47 s | `dd if=testfile_4k of=/dev/null bs=4K count=262144 iflag=direct` |

### 3.2 FIO随机IO测试结果

#### 3.2.1 不同块大小随机读写性能

| 块大小 | 读写模式 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|--------|----------|------|------------|--------------|-------------|------|
| 4K | 随机读 | 285,000 | 1,113 | 35 | 78 | `fio --name=4k_random_read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 4K | 随机写 | 195,000 | 761 | 51 | 125 | `fio --name=4k_random_write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 8K | 随机读写 | 145,000 | 1,133 | 69 | 156 | `fio --name=8k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=8k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 16K | 随机读写 | 78,000 | 1,219 | 128 | 285 | `fio --name=16k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=16k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 64K | 随机读写 | 22,500 | 1,406 | 444 | 963 | `fio --name=64k_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=64k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 1M | 随机读写 | 1,850 | 1,850 | 5,405 | 11,200 | `fio --name=1m_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=1m --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 4M | 随机读写 | 485 | 1,940 | 20,618 | 42,500 | `fio --name=4m_random_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4m --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |

#### 3.2.2 队列深度对性能的影响

| 队列深度 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|----------|------|------------|--------------|-------------|------|
| 1 | 28,500 | 111 | 35 | 65 | `fio --name=4k_qd1 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=1 --numjobs=1 --runtime=60 --group_reporting` |
| 4 | 115,000 | 449 | 35 | 72 | `fio --name=4k_qd4 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=4 --numjobs=1 --runtime=60 --group_reporting` |
| 8 | 195,000 | 761 | 41 | 85 | `fio --name=4k_qd8 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=8 --numjobs=1 --runtime=60 --group_reporting` |
| 16 | 285,000 | 1,113 | 56 | 125 | `fio --name=4k_qd16 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=16 --numjobs=1 --runtime=60 --group_reporting` |
| 32 | 320,000 | 1,250 | 100 | 235 | `fio --name=4k_qd32 --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --iodepth=32 --numjobs=1 --runtime=60 --group_reporting` |

#### 3.2.3 混合读写比例测试结果

| 读写比例 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|----------|------|------------|--------------|-------------|------|
| 100%读 | 285,000 | 1,113 | 35 | 78 | `fio --name=100read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 70%读30%写 | 245,000 | 957 | 41 | 95 | `fio --name=70read_30write --ioengine=libaio --rw=randrw --rwmixread=70 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 50%读50%写 | 220,000 | 859 | 45 | 115 | `fio --name=50read_50write --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 30%读70%写 | 205,000 | 801 | 49 | 135 | `fio --name=30read_70write --ioengine=libaio --rw=randrw --rwmixread=30 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 100%写 | 195,000 | 761 | 51 | 125 | `fio --name=100write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |

#### 3.2.4 并发测试结果

| 并发数 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |
|--------|------|------------|--------------|-------------|------|
| 1 | 220,000 | 859 | 45 | 115 | `fio --name=1job --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting` |
| 2 | 385,000 | 1,504 | 52 | 135 | `fio --name=2jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=2 --runtime=60 --group_reporting` |
| 4 | 650,000 | 2,539 | 61 | 165 | `fio --name=4jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=4 --runtime=60 --group_reporting` |
| 8 | 980,000 | 3,828 | 82 | 225 | `fio --name=8jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=8 --runtime=60 --group_reporting` |
| 16 | 1,250,000 | 4,883 | 128 | 365 | `fio --name=16jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=16 --runtime=60 --group_reporting` |
| 32 | 1,450,000 | 5,664 | 221 | 625 | `fio --name=32jobs --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=1G --numjobs=32 --runtime=60 --group_reporting` |

### 3.3 关键性能指标汇总

| 测试类型 | 最佳性能 | 平均性能 | 最差性能 | 性能波动率 |
|----------|----------|----------|----------|------------|
| 顺序读取速度 | 3200 MB/s | 2913 MB/s | 2200 MB/s | 12.5% |
| 顺序写入速度 | 2850 MB/s | 2518 MB/s | 1850 MB/s | 15.8% |
| 4K随机读IOPS | 320,000 | 285,000 | 28,500 | 8.7% |
| 4K随机写IOPS | 195,000 | 195,000 | 195,000 | 0% |
| 平均延迟 | 35 μs | 45 μs | 221 μs | 22.2% |
| 99%延迟 | 65 μs | 115 μs | 625 μs | 43.5% |

### 3.4 性能波动分析

#### 3.4.1 测试过程中的性能变化

**观察到的性能波动现象：**
- 在高并发测试中，延迟波动较为明显，99%延迟从65μs增长到625μs
- 顺序读写性能在不同块大小下有明显差异，4K块大小性能下降约30%
- 随机写性能相对稳定，各种测试场景下波动较小

#### 3.4.2 多次测试结果对比

| 测试轮次 | 4K随机读IOPS | 4K随机写IOPS | 顺序读(MB/s) | 顺序写(MB/s) |
|----------|--------------|--------------|--------------|-------------|
| 第1次 | 285,000 | 195,000 | 3200 | 2850 |
| 第2次 | 282,000 | 193,000 | 3180 | 2820 |
| 第3次 | 288,000 | 197,000 | 3220 | 2880 |
| 平均值 | 285,000 | 195,000 | 3200 | 2850 |
| 标准差 | 3,000 | 2,000 | 20 | 30 |
| 变异系数 | 1.1% | 1.0% | 0.6% | 1.1% |

---

## 4. 结论与建议

### 4.1 存储性能评估

#### 4.1.1 整体性能水平

**顺序读写性能：**
- 顺序读取速度：3200 MB/s，表现优秀
- 顺序写入速度：2850 MB/s，表现优秀
- 性能等级：优秀

**随机IO性能：**
- 4K随机读IOPS：285,000，表现优秀
- 4K随机写IOPS：195,000，表现良好
- 延迟表现：平均35μs，99%延迟78μs，表现优秀
- 性能等级：优秀

#### 4.1.2 性能特点分析

**优势：**
- 顺序读写性能优异，适合大文件处理和流媒体应用
- 4K随机读IOPS表现突出，适合数据库OLTP应用
- 低延迟特性，适合对响应时间敏感的应用
- 多并发场景下性能扩展性良好

**劣势：**
- 随机写性能相对读性能有一定差距
- 高并发场景下延迟波动较大
- 小块大小IO性能有所下降

### 4.2 业务适用性分析

#### 4.2.1 适合运行的业务类型

**数据库应用：**
- **OLTP数据库**：✅ 非常适合，4K随机读IOPS达到285K，远超一般OLTP需求(>10K)
- **OLAP数据库**：✅ 非常适合，顺序读性能3200MB/s，满足大数据分析需求
- **NoSQL数据库**：✅ 适合，混合读写性能良好，支持各种读写比例

**Web应用：**
- **高并发Web系统**：✅ 非常适合，多并发测试显示良好的扩展性
- **内容管理系统**：✅ 适合，文件读写性能优异
- **电商平台**：✅ 适合，混合负载性能表现良好

**流媒体应用：**
- **视频点播**：✅ 非常适合，顺序读性能3200MB/s，支持高清视频流
- **直播系统**：✅ 适合，写入性能和低延迟满足实时需求
- **音频处理**：✅ 适合，小文件性能良好

**大数据应用：**
- **数据仓库**：✅ 非常适合，大块顺序读写性能优异
- **日志分析**：✅ 适合，写入性能满足日志收集需求
- **机器学习**：✅ 适合，随机读性能支持模型训练数据访问

**虚拟化应用：**
- **虚拟机存储**：✅ 非常适合，混合负载性能优异
- **容器存储**：✅ 适合，小文件和随机IO性能良好

#### 4.2.2 不适合的业务场景

- 对成本极度敏感的大容量归档存储（性能过剩）
- 纯写入密集型应用（写性能相对读性能有差距）

### 4.3 潜在瓶颈分析

#### 4.3.1 性能瓶颈识别

**IOPS瓶颈：**
- 当前4K随机读IOPS：285,000
- 当前4K随机写IOPS：195,000
- 瓶颈分析：写IOPS相对读IOPS有31%的性能差距，可能成为写密集应用的瓶颈

**带宽瓶颈：**
- 当前顺序读带宽：3200 MB/s
- 当前顺序写带宽：2850 MB/s
- 瓶颈分析：接近NVMe SSD理论性能上限，暂无明显瓶颈

**延迟瓶颈：**
- 当前平均延迟：35 μs
- 当前99%延迟：78 μs
- 瓶颈分析：高并发场景下延迟增长明显，可能影响延迟敏感应用

#### 4.3.2 瓶颈成因分析

**硬件层面：**
- NVMe SSD已达到较高性能水平，硬件瓶颈不明显
- 可能受限于PCIe通道带宽或SSD控制器性能

**软件层面：**
- 默认IO调度器可能不是最优选择
- 文件系统参数可能需要针对性优化

**系统层面：**
- 高并发场景下可能存在CPU调度开销
- 内存缓存策略可能需要调整

### 4.4 优化建议

#### 4.4.1 硬件优化建议

**存储硬件：**
- 当前NVMe SSD性能已经很好，短期内无需升级
- 如需进一步提升，可考虑企业级NVMe SSD或NVMe RAID

**系统硬件：**
- CPU性能充足，无需升级
- 内存容量可适当增加以提供更大的缓存空间

#### 4.4.2 软件优化建议

**操作系统优化：**
- 调整IO调度器为`none`或`mq-deadline`：`echo none > /sys/block/nvme0n1/queue/scheduler`
- 优化内核参数：`vm.dirty_ratio=5`, `vm.dirty_background_ratio=2`

**应用层优化：**
- 数据库应用建议使用直接IO模式
- 适当调整应用层缓存大小和策略

#### 4.4.3 配置优化建议

**IO调度器：**
- 当前调度器：mq-deadline
- 推荐调度器：none（对于NVMe SSD）
- 优化命令：`echo none > /sys/block/nvme0n1/queue/scheduler`

**文件系统参数：**
- 挂载参数优化：`noatime,nodiratime,discard`
- 考虑使用XFS文件系统以获得更好的大文件性能

**系统参数：**
- 调整`/proc/sys/vm/dirty_ratio`为5
- 调整`/proc/sys/vm/dirty_background_ratio`为2
- 增加`ulimit -n`到65536

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
| 平均延迟 | 100 μs | 200 μs | 根据业务需求设定 |
| 99%延迟 | 500 μs | 1000 μs | 根据业务需求设定 |
| 队列深度 | 16 | 32 | 避免过度排队 |

---

## 5. 附录

### 5.1 原始测试数据

#### 5.1.1 DD命令原始输出

**顺序写入测试原始数据：**
```
$ dd if=/dev/zero of=testfile_1g bs=1G count=1 oflag=direct
1+0 records in
1+0 records out
1073741824 bytes (1.1 GB, 1.0 GiB) copied, 0.376648 s, 2.9 GB/s

$ dd if=/dev/zero of=testfile_4g bs=1G count=4 oflag=direct
4+0 records in
4+0 records out
4294967296 bytes (4.3 GB, 4.0 GiB) copied, 1.47832 s, 2.9 GB/s
```

**顺序读取测试原始数据：**
```
$ echo 3 > /proc/sys/vm/drop_caches
$ dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct
1+0 records in
1+0 records out
1073741824 bytes (1.1 GB, 1.0 GiB) copied, 0.335441 s, 3.2 GB/s
```

#### 5.1.2 FIO命令原始输出

**4K随机读测试原始数据：**
```json
{
  "fio version" : "fio-3.36",
  "timestamp" : 1705123456,
  "jobs" : [
    {
      "jobname" : "4k_random_read",
      "read" : {
        "io_bytes" : 70254592000,
        "io_kbytes" : 68608000,
        "bw_bytes" : 1170909866,
        "bw" : 1143466,
        "iops" : 285866.5,
        "runtime" : 60001,
        "total_ios" : 17152000,
        "lat_ns" : {
          "min" : 15234,
          "max" : 156789,
          "mean" : 34567.89,
          "stddev" : 12345.67,
          "percentile" : {
            "99.000000" : 78000
          }
        }
      }
    }
  ]
}
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

echo "开始存储性能测试..."
echo "测试目录: $TEST_DIR"
echo "测试大小: $TEST_SIZE"
echo "运行时间: $RUNTIME 秒"
echo "==========================================="

# DD顺序测试
echo "开始DD顺序写入测试..."
dd if=/dev/zero of=testfile_1g bs=1G count=1 oflag=direct

echo "清除系统缓存..."
echo 3 > /proc/sys/vm/drop_caches

echo "开始DD顺序读取测试..."
dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct

# FIO随机测试
echo "开始FIO 4K随机读测试..."
fio --name=4k_random_read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=$TEST_SIZE --numjobs=1 --runtime=$RUNTIME --group_reporting --output-format=json > 4k_read.json

echo "开始FIO 4K随机写测试..."
fio --name=4k_random_write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 --size=$TEST_SIZE --numjobs=1 --runtime=$RUNTIME --group_reporting --output-format=json > 4k_write.json

echo "开始FIO混合读写测试..."
fio --name=4k_mixed_rw --ioengine=libaio --rw=randrw --rwmixread=50 --bs=4k --direct=1 --size=$TEST_SIZE --numjobs=1 --runtime=$RUNTIME --group_reporting --output-format=json > 4k_mixed.json

# 清理测试文件
echo "清理测试文件..."
rm -f testfile_*

echo "==========================================="
echo "测试完成！结果文件："
ls -la *.json
echo "请查看JSON文件获取详细测试结果。"
```

### 5.3 性能基准参考

#### 5.3.1 不同存储类型性能基准

| 存储类型 | 顺序读(MB/s) | 顺序写(MB/s) | 4K随机读IOPS | 4K随机写IOPS | 延迟(μs) |
|----------|--------------|--------------|--------------|--------------|----------|
| SATA SSD | 500-550 | 450-500 | 80K-100K | 70K-90K | 50-100 |
| **NVMe SSD（本次测试）** | **3200** | **2850** | **285K** | **195K** | **35** |
| SATA HDD | 100-200 | 100-180 | 100-200 | 100-150 | 5000-15000 |
| SAS HDD | 150-250 | 150-220 | 200-400 | 150-300 | 3000-10000 |

#### 5.3.2 业务场景性能要求

| 业务场景 | IOPS要求 | 延迟要求 | 带宽要求 | 本次测试是否满足 |
|----------|----------|----------|----------|------------------|
| OLTP数据库 | >10K | <1ms | >100MB/s | ✅ 远超要求 |
| OLAP数据库 | >1K | <10ms | >500MB/s | ✅ 远超要求 |
| Web应用 | >5K | <5ms | >200MB/s | ✅ 远超要求 |
| 流媒体 | >1K | <100ms | >1GB/s | ✅ 满足要求 |
| 文件服务 | >2K | <10ms | >300MB/s | ✅ 远超要求 |

---

**报告生成时间：** 2024-01-15 14:30:00
**测试工具版本：** dd 8.32, fio 3.36, Python 3.12.3
**报告版本：** v1.0