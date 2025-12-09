#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shlex
from datetime import datetime

import json


def load_cluster(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_remote_command(remote_workdir: str, start_time_utc_min: str, main_args: str) -> str:
    # 统一到分钟：补齐秒为00
    dt = datetime.strptime(start_time_utc_min, '%Y-%m-%d %H:%M')
    start_str = dt.strftime('%Y-%m-%d %H:%M:00')
    # 构造远端一次性后台任务
    cmd = (
        f"bash -lc 'cd {shlex.quote(remote_workdir)}; "
        f"T=$(date -u -d \"{start_str}\" +%s); D=$((T-$(date -u +%s))); "
        f"(sleep $D; python3 main.py {main_args}) >/dev/null 2>&1 &'"
    )
    return cmd


def ssh_run(host: str, user: str, auth: dict, remote_cmd: str):
    if auth.get('type') == 'key':
        key = os.path.expanduser(auth.get('value'))
        base = [
            'ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', f"{user}@{host}", remote_cmd
        ]
        return subprocess.run(base, capture_output=True, text=True)
    elif auth.get('type') == 'password':
        pwd = auth.get('value')
        base = [
            'sshpass', '-p', pwd, 'ssh', '-o', 'StrictHostKeyChecking=no', f"{user}@{host}", remote_cmd
        ]
        return subprocess.run(base, capture_output=True, text=True)
    else:
        raise RuntimeError('未知认证类型，需为 key 或 password')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='定时下发远端测试')
    parser.add_argument('--config', default='config/cluster.json')
    parser.add_argument('--args', required=True, help='传递给 main.py 的参数字符串')
    args = parser.parse_args()

    cfg = load_cluster(args.config)
    remote_workdir = cfg.get('remote_workdir', '/data/volume-performance-testing')
    start_time = cfg['start_time_utc']
    remote_cmd = build_remote_command(remote_workdir, start_time, args.args)

    errors = []
    for vm in cfg['vms']:
        host = vm['host']
        user = vm['user']
        auth = vm['auth']
        r = ssh_run(host, user, auth, remote_cmd)
        if r.returncode != 0:
            errors.append((host, r.stderr.strip()))
        else:
            print(f"[OK] 下发到 {host}")

    if errors:
        print("[WARN] 下发存在失败主机：")
        for h, e in errors:
            print(f" - {h}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
