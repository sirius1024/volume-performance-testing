# 3pNv 使用预览

本预览说明如何在 3 台物理机（p=3）上，使用 N 台虚拟机（v=N）并行执行存储性能测试，并在本地集中归集、合并与对比报告。保持与单机一致的执行习惯：远端仅运行 `python3 main.py <你的参数>`，不引入额外路径与工具。

## 一、准备配置
- 编辑 `config/cluster.json`
  - `p`: 物理机数量（人工填写，如 3）
  - `start_time_utc`: 统一启动时间（UTC，分钟级，例如 `2025-12-09 10:05`）
  - `remote_workdir`: 远端代码目录（默认 `/data/volume-performance-testing`）
  - `vms`: 虚拟机列表（每行一个 `host/user/auth`，`auth.type` 为 `key` 或 `password`）

示例：
```json
{
  "p": 3,
  "start_time_utc": "2025-12-09 10:05",
  "remote_workdir": "/data/volume-performance-testing",
  "vms": [
    { "host": "10.0.0.11", "user": "vmuser", "auth": { "type": "key", "value": "~/.ssh/id_rsa" } },
    { "host": "10.0.0.12", "user": "vmuser", "auth": { "type": "password", "value": "PASSWORD" } },
    { "host": "10.0.0.13", "user": "vmuser", "auth": { "type": "key", "value": "~/.ssh/id_rsa" } }
  ]
}
```

## 二、定时同时启动（3pNv）
在控制端执行一次下发：
```
python3 tools/dispatch.py --config config/cluster.json --args "<你的 main.py 参数>"
```
- 远端会在 `start_time_utc` 到点后执行：`python3 main.py <你的参数>`
- 每台虚拟机会在 `test_data/reports/<YYYYMMDD-HHMM>/` 生成：
  - Markdown 主报告：`storage_performance_report_<STAMP>.md`（或 `-quick.md`）
  - JSON 数据：`report.json`
- 说明：`<STAMP>` 即分钟级目录名（UTC），如 `20251209-1005`

## 三、归集与合并
1）归集（自动用 `start_time_utc` 推导目录）
```
python3 tools/collect.py --config config/cluster.json
```
- 将每台的 `*.md` 与 `*.json` 回收到：
  - `test_data/reports/centralized/<STAMP>/raw/<IP>.md`
  - `test_data/reports/centralized/<STAMP>/raw/<IP>.json`
- 同一分钟重复归集会覆盖该分钟目录

2）合并（基于归集的 JSON）
```
python3 tools/aggregate.py --config config/cluster.json
```
- 生成 `test_data/reports/centralized/<STAMP>/aggregate.json`
- 规则：
  - IOPS/带宽：同 `name` 求和
  - 延迟：同 `name` 算术平均
- 元信息：
  - `p` 来自 `config/cluster.json`
  - `vm_count` 自动为 `raw/*.json` 的份数（即“几 v”）
  - `sources` 列出来源虚拟机 IP

## 四、对比报告
- 仅支持同类型（同 `p`）聚合 JSON 的对比
- 自动选择最新与上一次：
```
python3 tools/compare.py --auto
```
- 或指定两次分钟目录：
```
python3 tools/compare.py --baseline 20251201-1005 --current 20251209-1005
```
- 输出：`test_data/reports/centralized/compare/<baseline>_vs_<current>.json`
  - IOPS/带宽按“越大越好”的差值与百分比
  - 延迟按“越小越好”的差值与百分比，标注 `improved/declined/flat`

## 五、注意事项
- 远端必须在 `remote_workdir` 部署本项目代码，并可执行 `python3 main.py <你的参数>` 产出报告
- 时间统一为 UTC 的分钟级目录名；无需 `run_id`
- 密码登录仅在不得已时使用，优先免密 `key`
- 失败虚拟机不会阻塞聚合，对应 IP 会在合并元信息中缺失或在归集日志中提示

## 六、快速自检
- 在本地运行单机快速测试：
```
python3 tests/test_report_paths.py
```
- 预期输出：在 `test_data/reports/<当前UTC分钟>/` 生成 `fio_detailed_report-quick.md`、主报告 `storage_performance_report_<STAMP>-quick.md` 和 `report.json`

如需我替你填入真实 IP 与认证配置，提供 3 台虚拟机的信息后即可直接按上述命令执行 3p3v。 
