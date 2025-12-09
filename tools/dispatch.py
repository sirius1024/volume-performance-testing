#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shlex
from datetime import datetime

import json
import argparse


def load_cluster(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_remote_command(remote_workdir: str, start_time_utc_min: str, main_args: str, sudo: bool, stream: bool) -> str:
    dt = datetime.strptime(start_time_utc_min, '%Y-%m-%d %H:%M')
    start_str = dt.strftime('%Y-%m-%d %H:%M:00')
    stamp = dt.strftime('%Y%m%d-%H%M')
    sudo_prefix = 'sudo -E ' if sudo else ''
    # 统一分钟戳：将调度的 UTC 分钟戳传递给 main.py，确保报告目录与 run.log 一致
    if '--stamp' not in f" {main_args} ":
        main_args = (main_args + f" --stamp {stamp}").strip()
    log_dir = f"test_data/reports/{stamp}"
    log_file = f"{log_dir}/run.log"
    if stream:
        cmd = (
            f"bash -lc 'cd {shlex.quote(remote_workdir)}; "
            f"T=$(date -u -d \"{start_str}\" +%s); D=$((T-$(date -u +%s))); "
            f"{sudo_prefix}mkdir -p {log_dir}; if [ $D -gt 0 ]; then sleep $D; fi; "
            f"{sudo_prefix}python3 -u main.py {main_args} 2>&1 | {sudo_prefix}tee -a {log_file}'"
        )
    else:
        cmd = (
            f"bash -lc 'cd {shlex.quote(remote_workdir)}; "
            f"T=$(date -u -d \"{start_str}\" +%s); D=$((T-$(date -u +%s))); "
            f"{sudo_prefix}mkdir -p {log_dir}; "
            f"nohup bash -c \"if [ \\$D -gt 0 ]; then sleep \\$D; fi; {sudo_prefix}python3 -u main.py {main_args} 2>&1 | {sudo_prefix}tee -a {log_file}\" >>/tmp/volume-test-error.log 2>&1 &'"
        )
    return cmd


def ssh_run(host: str, user: str, auth: dict, remote_cmd: str):
    if auth.get('type') == 'key':
        key = os.path.expanduser(auth.get('value'))
        base = [
            'ssh', '-T', '-i', key, '-o', 'StrictHostKeyChecking=no', f"{user}@{host}", remote_cmd
        ]
        return subprocess.run(base, capture_output=True, text=True)
    elif auth.get('type') == 'password':
        pwd = auth.get('value')
        base = [
            'sshpass', '-p', pwd, 'ssh', '-T', '-o', 'StrictHostKeyChecking=no', f"{user}@{host}", remote_cmd
        ]
        return subprocess.run(base, capture_output=True, text=True)
    else:
        raise RuntimeError('未知认证类型，需为 key 或 password')


def _extract_main_args() -> str:
    argv = sys.argv[1:]
    if '--' in argv:
        idx = argv.index('--')
        return ' '.join(argv[idx+1:]).strip()
    if '--args' in argv:
        idx = argv.index('--args')
        return ' '.join(argv[idx+1:]).strip()
    return ''


def main():
    parser = argparse.ArgumentParser(description='定时下发远端测试', allow_abbrev=False)
    parser.add_argument('--config', default='config/cluster.json')
    parser.add_argument('--stream', action='store_true')
    args, unknown = parser.parse_known_args()

    cfg = load_cluster(args.config)
    remote_workdir = cfg.get('remote_workdir', '/data/volume-performance-testing')
    start_time = cfg['start_time_utc']
    stream = args.stream
    # 提取 main.py 参数（支持 "--" 或 "--args" 两种方式）
    if '--' in unknown:
        i = unknown.index('--')
        main_args = ' '.join(unknown[i+1:]).strip()
    elif '--args' in unknown:
        i = unknown.index('--args')
        main_args = ' '.join(unknown[i+1:]).strip()
    else:
        main_args = _extract_main_args()
    if (not stream) and (' --stream' in f" {main_args}"):
        pass
    sudo_default = bool(cfg.get('sudo', False))
    errors = []
    for vm in cfg['vms']:
        host = vm['host']
        user = vm['user']
        auth = vm['auth']
        sudo = bool(vm.get('sudo', sudo_default))
        remote_cmd = build_remote_command(remote_workdir, start_time, main_args, sudo, stream)
        print(f"EXEC {user}@{host} [{auth.get('type','unknown')}]: {remote_cmd}")
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
