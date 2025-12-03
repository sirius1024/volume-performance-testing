# 存储性能测试工具 (Storage Performance Testing Tool) v2.0

这是一个专业的虚拟机与服务器存储性能测试工具，集成了 DD 与 FIO 两种业界标准工具，提供全面、自动化、可重复的存储性能评估与分析。该项目在设计上兼顾使用者与贡献者体验，遵循清晰的模块化架构与标准化工程流程。

## 🌟 主要特性

- 全面 FIO 测试矩阵：支持 480 组合（8×6×2×5），覆盖块大小、队列深度、读写比例与并发数。
- DD 顺序 I/O 测试：支持 Direct 与 Sync/DSync 模式的顺序读写。
- 自动化报告生成：输出包含系统信息、测试摘要与详细指标的 Markdown 报告。
- 灵活测试模式：支持快速模式（Quick）与完整模式，适用开发验证与基准评估。
- 系统信息收集：自动采集 OS、内核、CPU、内存、磁盘与文件系统信息。
- 友好 CLI：简洁直观的命令行参数与默认值，便于集成到 CI/CD。

## 📦 项目结构

```
volume-performance-testing/
├─ main.py                  # 主控脚本，解析参数、调度测试、生成报告
├─ common.py                # 通用类型与工具：Logger、TestResult、系统信息等
├─ dd_test.py               # DD 测试执行器：顺序写、同步写、顺序读
├─ fio_test.py              # FIO 测试执行器：完整矩阵与快速场景
├─ generate_fio_commands.py # FIO 命令生成辅助（可复用/调试）
├─ fio_test.md              # FIO 测试说明与补充材料
├─ tools/                   # 辅助工具（如产品检查、命令导出）
│  ├─ check_fio_product.py
│  └─ dump_commands.py
├─ tests/                   # 测试用例（示例：路径与报告检查）
│  └─ test_report_paths.py
├─ README.md                # 原版说明
├─ README-v2.md             # 增强版说明（当前文件）
└─ LICENSE                  # 许可证
```

## 🧩 核心模块说明

- `main.py`：
    - 负责命令行参数解析与任务编排（DD、FIO、或两者）。
    - 初始化 `DDTestRunner` 与 `FIOTestRunner`，执行测试并收集结果。
    - 内置 `ReportGenerator` 生成综合报告：系统信息、测试详情与摘要。
    - 关键参数：`--dd-only`、`--fio-only`、`--quick`、`--runtime`、`--test-dir`、`--output`、`--cleanup`、`--fio-info`。

- `common.py`：
    - `TestResult`：统一测试结果数据结构（名称、类型、块大小、队列深度、IOPS/吞吐、耗时、错误等）。
    - `Logger`：统一日志输出与级别管理（info/warn/error）。
    - `SystemInfoCollector`：采集系统/硬件信息（OS 内核、CPU、内存、文件系统、磁盘容量等）。
    - `ensure_directory` / `clear_system_cache`：目录确保与缓存清理等通用工具。

- `dd_test.py`（DDTestRunner）：
    - 顺序写：`oflag=direct`，不同块大小与文件大小组合。
    - 同步写：`oflag=direct,dsync` 与 `oflag=dsync` 两类场景。
    - 顺序读：`iflag=direct`，在生成的测试文件上验证读取吞吐。
    - 输出包括吞吐率（MB/s）与耗时（秒），并记录命令行与错误信息。

- `fio_test.py`（FIOTestRunner）：
    - 完整矩阵：块大小（4k,8k,16k,32k,64k,128k,1m,4m）× 队列深度（1,2,4,8,16,32）× 并发（按 iodepth 映射 1/4/8，其中 qd=32→[4,8]）× 读写比例（0/25/50/75/100）。
    - 快速场景：精选代表性组合用于 CI 与开发验证（运行时间短）。
    - 指标：IOPS、带宽（MB/s）、延迟（us/ms），支持 JSON 输出并解析指标到 `TestResult`。
    - 超时保护：基于 `runtime + 240` 的命令执行超时与错误处理。
    - 文件大小：统一 `--size=10G`。

## 🏗️ 架构与执行流程

- 启动与参数解析：`main.py` 使用 `argparse` 解析 CLI 参数，决定测试范围与模式。
- 资源准备：确保 `--test-dir` 可写，必要时创建目录；可选清除系统缓存。
- 测试执行：
    - DD：顺序写（direct）、同步写（direct+dsync/dsync）、顺序读（direct）。
    - FIO：按矩阵或快速场景运行，为每场景生成 JSON 文件并记录完整命令；核心业务场景如配置则在报告中单独呈现。
- 结果汇总：将 `TestResult` 列表交由 `ReportGenerator` 生成 Markdown 报告。
- 交互提示：当完整 FIO 耗时预计超过 10 分钟，进行用户确认。
- 收尾与清理：根据 `--cleanup` 删除测试生成文件，保持环境整洁。

### 数据模型与约定

- `TestResult` 统一承载：`test_name`、`test_type`、`block_size`、`queue_depth`、`numjobs`、`rwmix_read`、`throughput_mbps`、`iops`、`latency_ms`、`duration_seconds`、`command`、`error_message`。
- 报告结构：
    - 头部：标题与生成时间。
    - 系统信息：OS/内核/CPU/内存/文件系统/磁盘容量。
    - 核心业务场景：如配置则展示（位于系统信息之后、DD/FIO结果之前）。
    - DD 结果：概览（成功/失败数量）与表格（块大小/文件大小/吞吐/耗时）。
    - FIO 结果：概览与关键指标（IOPS/带宽/延迟）。
    - 摘要：成功统计与可能异常。

## 🚀 快速开始

```bash
git clone <repository-url>
cd volume-performance-testing
python3 main.py --quick
```

## 📖 使用指南

- `--all`：运行所有测试（DD + FIO，默认）。
- `--dd-only`：仅运行 DD 测试。
- `--fio-only`：仅运行 FIO 测试。
- `--quick`：快速模式，仅运行代表性测试场景（FIO 运行时间短）。
- `--runtime SEC`：FIO 每个场景运行时间（秒），默认 3。
- `--test-dir DIR`：测试文件目录，默认 `./test_data`。
- `--cleanup`：测试完成后清理测试文件。
- `--output FILE`：指定报告输出路径；未指定时自动生成到 `./reports` 或当前目录。
- `--fio-info`：打印 FIO 测试矩阵信息（场景规模、预计耗时）。

### 常见命令

```bash
# 仅 DD 顺序读写
python3 main.py --dd-only

# 仅 FIO 随机 I/O，运行 10 秒
python3 main.py --fio-only --runtime 10

# 完整测试并清理临时文件
python3 main.py --all --cleanup

# 查看 FIO 测试矩阵规模与预计耗时
python3 main.py --fio-info
```

## 📊 测试详情

- FIO：
    - 块大小：`4k, 8k, 16k, 32k, 64k, 128k, 1m, 4m`
    - 队列深度：`1, 2, 4, 8, 16, 32`
    - 读写比例：`0, 25, 50, 75, 100`（randwrite/randrw/randread）
    - 并发：按队列深度映射 `1/4/8`（`qd=32 → 4,8`）
    - 大小与超时：`--size=10G`，执行超时 `runtime+240`
    - 兼容性：在 `9p` 文件系统自动回退 `ioengine` 为 `psync`，其他环境使用 `libaio`

- DD：
    - 顺序写（direct）与同步写（direct+dsync / dsync）
    - 顺序读（direct），在已写入的测试文件上验证吞吐

## 📝 报告输出

生成的报告将包含：

- 测试概览：总测试数、成功/失败数量、总耗时。
- 系统信息：OS、内核、CPU、内存、文件系统、磁盘容量与可用空间。
- 核心业务场景：核心 FIO/DD 场景的汇总与明细表。
- DD 结果：表格形式列出块大小、文件大小、吞吐（MB/s）、耗时（秒）。
- FIO 结果：IOPS、带宽、延迟分布（如平均/99%）。
- 测试摘要：关键结论与异常说明。

## 🤝 贡献指南

- 环境准备：确保安装 `python3`、`fio`，Linux 建议具备 sudo 权限以执行缓存清理。
- 开发流程：
    - 创建分支：`feat/*`、`fix/*`、`docs/*`。
    - 保持代码通过本地自测（运行 `--quick` 与必要场景）。
    - 编写或更新文档（README / fio_test.md），并在 PR 中说明变更影响。
- 代码规范：
    - 保持模块内的日志与异常处理一致（使用 `Logger`）。
    - 统一 `TestResult` 字段，避免临时扩展未入规范。
    - 提交前运行格式化与静态检查（如 `flake8`/`ruff`，可在后续引入）。
- 测试与验证：在 `tests/` 中补充单测/集成测试；尽量模拟常见设备/文件系统环境。
- Issue 与讨论：欢迎在 Issue 中提出新的测试场景建议或兼容性问题。

## ⚠️ 注意事项

- 数据安全：测试会在 `--test-dir`（默认 `./test_data`）生成大量临时文件，请确保磁盘空间充足。
- 性能影响：测试过程产生高强度 I/O，请避开生产高峰时段运行。
- 权限需求：清除系统缓存与部分 FIO 场景可能需要更高权限（sudo）。
- 设备选择：如在虚拟化/云环境中测试，请明确目标卷/设备与挂载参数（如 `noatime`）。

## 📄 许可证

Apache License 2.0
## 📚 核心业务场景配置

- 维护位置：`config/core_scenarios.yaml`
- 内容结构：包含核心场景字段（`name/rw/bs/iodepth/numjobs/rwmixread/runtime/size` 等）
- 执行策略：DD 快速/完整均执行核心场景；FIO 核心场景当前未默认启用（需在运行器中调用）；报告在系统信息之后单独呈现
- 清单导出：`python3 tools/dump_commands.py` 在“CORE 场景（YAML）”分节显示摘要
