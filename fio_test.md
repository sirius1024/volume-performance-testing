# FIO测试命令详细列表

> ⚠️ **注意**：本文档仅供参考。要获取与当前代码逻辑完全一致的最新命令清单，请运行：
> ```bash
> python3 tools/dump_commands.py
> ```
> 该工具会生成包含 DD 和 FIO 所有命令的 `commands_manifest.md` 文件。

本文档描述当前 FIO 测试矩阵与示例命令（同步实现）：
- **块大小**: 4k, 8k, 16k, 32k, 64k, 128k, 1m, 4m (8种)
- **队列深度**: 1, 2, 4, 8, 16, 32 (6种)
- **并发数**: 按队列深度映射 (2种)
  - iodepth=1,2,4: numjobs=1,4
  - iodepth=8,16: numjobs=4,8
  - iodepth=32: numjobs=4,8
- **读写比例**: 0%(纯写), 25%, 50%, 75%, 100%(纯读) (5种)

总计: 8 × 6 × 2 × 5 = **480 个测试场景**

## 测试命令表格

| 序号 | 块大小 | 队列深度 | 并发数 | 读写模式 | 读写比例 | 完整FIO命令 |
|------|--------|----------|--------|----------|----------|-------------|
| 1 | 4k | 1 | 1 | randwrite | 0% | fio --name=test --filename=fio_test_4k_1_1_0 --rw=randwrite --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=10G --output=fio_json_4k_1_1_0.json |
| 2 | 4k | 1 | 1 | randrw | 25% | fio --name=test --filename=fio_test_4k_1_1_25 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=25 |
| 3 | 4k | 1 | 1 | randrw | 50% | fio --name=test --filename=fio_test_4k_1_1_50 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=50 |
| 4 | 4k | 1 | 1 | randrw | 75% | fio --name=test --filename=fio_test_4k_1_1_75 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=75 |
| 5 | 4k | 1 | 1 | randread | 100% | fio --name=test --filename=fio_test_4k_1_1_100 --rw=randread --bs=4k --iodepth=1 --numjobs=1 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=10G --output=fio_json_4k_1_1_100.json |
| 6 | 4k | 1 | 4 | randwrite | 0% | fio --name=test --filename=fio_test_4k_1_4_0 --rw=randwrite --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=10G --output=fio_json_4k_1_4_0.json |
| 7 | 4k | 1 | 4 | randrw | 25% | fio --name=test --filename=fio_test_4k_1_4_25 --rw=randrw --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=25 |
| 8 | 4k | 1 | 4 | randrw | 50% | fio --name=test --filename=fio_test_4k_1_4_50 --rw=randrw --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=50 |
| 9 | 4k | 1 | 4 | randrw | 75% | fio --name=test --filename=fio_test_4k_1_4_75 --rw=randrw --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=1G --rwmixread=75 |
| 10 | 4k | 1 | 4 | randread | 100% | fio --name=test --filename=fio_test_4k_1_4_100 --rw=randread --bs=4k --iodepth=1 --numjobs=4 --runtime=3 --time_based --direct=1 --ioengine=libaio --group_reporting --output-format=json --size=10G --output=fio_json_4k_1_4_100.json |
| ... | ... | ... | ... | ... | ... | ... |

*(表格过长，仅展示部分。请运行工具生成完整清单)*

## 性能测试目标

这480个测试场景旨在全面评估存储系统在不同工作负载下的性能特征：

1. **IOPS性能**: 通过小块大小（4k-64k）测试随机I/O性能
2. **吞吐量性能**: 通过大块大小（1m）测试顺序I/O性能
3. **队列深度影响**: 评估不同并发级别对性能的影响
4. **读写混合**: 测试不同读写比例下的性能表现
5. **并发扩展性**: 比较单线程和多线程性能差异

通过这些全面的测试，可以深入了解存储系统的性能瓶颈和优化方向。
