# 3pNv 快速上手（面向用户）

面向需要“一次下发、三机并行、集中出报告”的用户说明。目标：在 3 台物理机（p=3）上的 N 台虚拟机（v=N）同时运行 `python3 main.py <参数>`，并在控制端自动归集与聚合，拿到 Markdown 与 JSON 报告。

## 你需要准备什么
- 在每台虚拟机（被测端）：安装 `python3`、`fio`、`coreutils`、`openssh-server`，并把本项目代码放到 `remote_workdir`（默认 `/data/volume-performance-testing`）。
- 在控制端（你现在所在机器）：安装 `python3`、`openssh-client`；若用密码认证，再安装 `sshpass`。
- 时间建议统一到 UTC 分钟级（NTP/chrony 非必需，但推荐）。

## 配置集群（1 分钟）
编辑 `config/cluster.json`，填入你的环境信息（不要提交真实凭据到 Git）：
```json
{
  "p": 3,
  "start_time_utc": "2025-12-09 10:05",
  "remote_workdir": "/data/volume-performance-testing",
  "sudo": true,
  "vms": [
    { "host": "10.0.0.11", "user": "ubuntu", "auth": { "type": "key", "value": "~/.ssh/id_rsa" } },
    { "host": "10.0.0.12", "user": "ubuntu", "auth": { "type": "password", "value": "PASSWORD" } },
    { "host": "10.0.0.13", "user": "ubuntu", "auth": { "type": "key", "value": "~/.ssh/id_rsa" } }
  ]
}
```
字段说明：
- `p`：物理机数量，仅用于聚合元信息显示。
- `start_time_utc`：统一启动时间（UTC，分钟级）；设为“当前或过去的分钟”可直接立即执行。
- `remote_workdir`：远端代码目录（每台 VM 需要已部署此项目）。
- `sudo`：是否用 `sudo -E` 运行；可在单机覆盖该字段。
- `vms`：虚拟机列表，每项给出 `host/user/auth`；`auth.type` 为 `key` 或 `password`。

## 一次下发，三机并行（30 秒）
下发命令（示例使用快速模式）：
```
python3 tools/dispatch.py --config config/cluster.json --args "--quick"
```
发生了什么：
- 控制端通过 SSH 把“到点即跑”的命令下发到每台 VM。
- 远端创建分钟目录 `test_data/reports/<STAMP>/` 并写入 `run.log`。
- 到点后运行 `python3 -u main.py --quick --stamp <STAMP>`，DD 与 FIO 在同一目录产出报告。

立即执行技巧：
- 把 `start_time_utc` 设为“当前或过去的 UTC 分钟”，调度会跳过等待直接启动。

## 快速验证（可选，10 秒）
```
python3 tools/verify.py --config config/cluster.json
```
它会检查每台 VM：
- `remote_workdir` 与 `main.py` 是否存在
- `python3`、`fio` 是否可用
- `sudo -n` 是否免密
- 能否写入分钟目录与 `run.log`，并查看运行中的 `main.py` 进程

## 归集与聚合（60–180 秒，取决于网络）
归集远端报告到本地：
```
python3 tools/collect.py --config config/cluster.json
```
本地产物：
- `test_data/reports/centralized/<STAMP>/raw/<IP>.md`
- `test_data/reports/centralized/<STAMP>/raw/<IP>.json`

生成聚合报告（自动输出 Markdown 与 JSON）：
```
python3 tools/aggregate.py --config config/cluster.json
```
本地产物：
- `test_data/reports/centralized/<STAMP>/aggregate.md`
- `test_data/reports/centralized/<STAMP>/aggregate.json`
说明：
- IOPS/带宽按相同 `name` 聚合求和；延迟按相同 `name` 求算术平均。
- 元信息包含 `p`、`vm_count`、`sources`（IP 列表）与时间戳。

## 对比历史（可选）
自动选择最新与上一次：
```
python3 tools/compare.py --auto
```
或指定两次分钟目录：
```
python3 tools/compare.py --baseline 20251201-1005 --current 20251209-1005
```
输出：`test_data/reports/centralized/compare/<baseline>_vs_<current>.json`

## 常见问题
- SSH 密码登录报错：控制端需安装 `sshpass`。
- 远端目录缺失：确保把项目代码部署到 `remote_workdir`，并能运行 `python3 main.py`。
- `fio` 不存在：在远端安装 `fio`（Ubuntu: `sudo apt install fio`；RHEL: `sudo yum install fio`）。
- `sudo` 需要密码：在远端配置免密或将 `sudo` 设为 `false`（可能影响需要特权的操作）。
- 归集不到文件：确认分钟戳 `<STAMP>` 与 `start_time_utc` 一致，以及网络与权限正常。

## 安全与协作
- `config/cluster.json` 含敏感信息，已在 `.gitignore` 忽略；请勿提交到仓库。
- 如需共享模板，使用 `config/cluster.example.json`。
- 优先使用密钥认证（`auth.type=key`），避免明文密码泄露风险。

## 期望的目录结构（参考）
```
test_data/
  reports/
    <STAMP>/
      storage_performance_report_<STAMP>-quick.md
      fio_detailed_report-quick.md
      report.json
      run.log
    centralized/
      <STAMP>/
        raw/
          <IP>.md
          <IP>.json
        aggregate.md
        aggregate.json
```

现在就可以把你的三台虚拟机信息填入 `config/cluster.json`，执行一次下发：
```
python3 tools/dispatch.py --config config/cluster.json --args "--quick"
```
等待完成后，直接运行归集与聚合两条命令，拿到集中化的 Markdown 与 JSON 报告。
