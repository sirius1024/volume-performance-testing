#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整的480个FIO测试命令表格

说明：本文件生成的是基线示例命令（统一 --size=10G，ioengine=libaio，--direct=1）。
实际执行时以 FIOTestRunner 为准，会根据文件系统（如 9p）自动回退
ioengine=psync，并在 randread/randrw 场景下使用 --direct=0。
"""

def generate_fio_commands_table():
    """生成完整的FIO测试命令表格"""
    
    # 测试配置矩阵（与运行器保持一致）
    block_sizes = ["4k", "8k", "16k", "32k", "64k", "128k", "1m", "4m"]
    queue_depths = [1, 2, 4, 8, 16, 32]
    
    # iodepth与numjobs的对应关系
    iodepth_numjobs_mapping = {
        1: [1, 4],
        2: [1, 4],
        4: [1, 4],
        8: [4, 8],
        16: [4, 8],
        32: [4, 8],
    }
    
    rwmix_ratios = [0, 25, 50, 75, 100]
    
    # 生成表格头部
    content = """# FIO测试命令详细列表

本文档包含完整的480个FIO测试场景的具体命令。测试矩阵包括：
- **块大小**: 4k, 8k, 16k, 32k, 64k, 128k, 1m, 4m (8种)
- **队列深度**: 1, 2, 4, 8, 16, 32 (6种)
- **并发数**: 根据队列深度动态配置 (2种)
  - iodepth=1,2,4: numjobs=1,4
  - iodepth=8,16: numjobs=4,8
  - iodepth=32: numjobs=4,8
- **读写比例**: 0%(纯写), 25%(25%读75%写), 50%(50%读50%写), 75%(75%读25%写), 100%(纯读) (5种)

总计: 8 × 6 × 2 × 5 = **480个测试场景**

## 测试命令表格

| 序号 | 块大小 | 队列深度 | 并发数 | 读写模式 | 读写比例 | 完整FIO命令 |
|------|--------|----------|--------|----------|----------|-------------|
"""
    
    scenario_count = 0
    
    for block_size in block_sizes:
        for queue_depth in queue_depths:
            numjobs_list = iodepth_numjobs_mapping[queue_depth]
            for numjobs in numjobs_list:
                for rwmix_read in rwmix_ratios:
                    scenario_count += 1
                    
                    # 确定测试类型和读写模式描述
                    if rwmix_read == 0:
                        test_type = "randwrite"
                        rwmix_desc = "0%"
                    elif rwmix_read == 100:
                        test_type = "randread"
                        rwmix_desc = "100%"
                    else:
                        test_type = "randrw"
                        rwmix_desc = f"{rwmix_read}%"
                    
                    # 构建FIO命令
                    test_file = f"fio_test_{block_size}_{queue_depth}_{numjobs}_{rwmix_read}"
                    
                    fio_command = [
                        "fio",
                        "--name=test",
                        f"--filename={test_file}",
                        f"--rw={test_type}",
                        f"--bs={block_size}",
                        f"--iodepth={queue_depth}",
                        f"--numjobs={numjobs}",
                        "--runtime=3",
                        "--time_based",
                        "--direct=1",
                        "--ioengine=libaio",
                        "--group_reporting",
                        "--output-format=json",
                        "--size=10G"
                    ]
                    
                    # 如果是混合读写，添加读写比例参数
                    if test_type == "randrw":
                        fio_command.append(f"--rwmixread={rwmix_read}")
                    
                    command_str = " ".join(fio_command)
                    
                    # 添加表格行
                    content += f"| {scenario_count} | {block_size} | {queue_depth} | {numjobs} | {test_type} | {rwmix_desc} | {command_str} |\n"
    
    # 添加说明部分
    content += """

## 命令参数说明

- `--name=test`: 测试任务名称
- `--filename=fio_test_*`: 测试文件名，包含块大小、队列深度、并发数和读写比例信息
- `--rw=`: 读写模式
  - `randread`: 随机读
  - `randwrite`: 随机写
  - `randrw`: 随机读写混合
- `--bs=`: 块大小（4k, 8k, 16k, 32k, 64k, 1m, 4m）
- `--iodepth=`: 队列深度（1, 2, 4, 8, 16, 32, 128）
- `--numjobs=`: 并发作业数（根据队列深度动态配置）
- `--runtime=3`: 每个测试运行3秒
- `--time_based`: 基于时间的测试
- `--direct=1`: 启用直接I/O，绕过系统缓存
- `--ioengine=libaio`: 使用Linux异步I/O引擎
- `--group_reporting`: 合并多个作业的报告
- `--output-format=json`: 输出JSON格式结果
- `--size=10G`: 测试文件大小10GB
- `--rwmixread=`: 读写混合模式下的读取百分比（仅用于randrw模式）

## 测试场景分布

### 按块大小分组
- **4k**: 60个测试场景（6种队列深度 × 2种并发 × 5种读写比例）
- **8k**: 60个测试场景
- **16k**: 60个测试场景
- **32k**: 60个测试场景
- **64k**: 60个测试场景
- **128k**: 60个测试场景
- **1m**: 60个测试场景
- **4m**: 60个测试场景

### 按读写模式分组
- **随机写(randwrite)**: 96个测试场景（8种块大小 × 6种队列深度 × 2种并发）
- **25%读75%写(randrw)**: 96个测试场景
- **50%读50%写(randrw)**: 96个测试场景
- **75%读25%写(randrw)**: 96个测试场景
- **随机读(randread)**: 96个测试场景

### 按队列深度分组
- **QD=1**: 80个测试场景（8种块大小 × 2种并发 × 5种读写比例）
- **QD=2**: 80个测试场景
- **QD=4**: 80个测试场景
- **QD=8**: 80个测试场景
- **QD=16**: 80个测试场景
- **QD=32**: 80个测试场景

### 按并发数分组
- **低并发(numjobs=1,4)**: 240个测试场景（iodepth=1,2,4时，8种块大小 × 2并发 × 5比例 × 3个QD）
- **中并发(numjobs=4,8)**: 240个测试场景（iodepth=8,16,32时，8种块大小 × 2并发 × 5比例 × 3个QD）

## 性能测试目标

这490个测试场景旨在全面评估存储系统在不同工作负载下的性能特征：

1. **IOPS性能**: 通过小块大小（4k-64k）测试随机I/O性能
2. **吞吐量性能**: 通过大块大小（1m）测试顺序I/O性能
3. **队列深度影响**: 评估不同并发级别对性能的影响
4. **读写混合**: 测试不同读写比例下的性能表现
5. **并发扩展性**: 比较单线程和多线程性能差异

通过这些全面的测试，可以深入了解存储系统的性能瓶颈和优化方向。
"""
    
    return content

if __name__ == "__main__":
    # 生成完整的FIO命令表格
    table_content = generate_fio_commands_table()
    
    # 写入文件
    with open("fio_test.md", "w", encoding="utf-8") as f:
        f.write(table_content)
    
    print(f"已生成完整的FIO测试命令表格，共480个测试场景")
    print(f"文件保存为: fio_test.md")
    print(f"文件大小: {len(table_content)} 字符")
