#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from datetime import datetime
import json


def load_cluster(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def stamp_from_start(start_time_utc_min: str) -> str:
    dt = datetime.strptime(start_time_utc_min, '%Y-%m-%d %H:%M')
    return dt.strftime('%Y%m%d-%H%M')


def scp_pull(host: str, user: str, auth: dict, remote_path: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    if auth.get('type') == 'key':
        key = os.path.expanduser(auth.get('value'))
        cmd = ['scp', '-i', key, '-o', 'StrictHostKeyChecking=no', f"{user}@{host}:{remote_path}", local_path]
    else:
        pwd = auth.get('value')
        cmd = ['sshpass', '-p', pwd, 'scp', '-o', 'StrictHostKeyChecking=no', f"{user}@{host}:{remote_path}", local_path]
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='归集远端报告')
    parser.add_argument('--config', default='config/cluster.json')
    args = parser.parse_args()

    cfg = load_cluster(args.config)
    start_time = cfg['start_time_utc']
    stamp = stamp_from_start(start_time)
    centralized = os.path.join('test_data', 'reports', 'centralized', stamp)
    raw_dir = os.path.join(centralized, 'raw')
    os.makedirs(raw_dir, exist_ok=True)

    # 本地项目的默认测试目录
    local_reports_dir = os.path.join('test_data', 'reports', stamp)

    errors = []
    for vm in cfg['vms']:
        host = vm['host']; user = vm['user']; auth = vm['auth']
        base_dir = os.path.join(cfg.get('remote_workdir', '/data/volume-performance-testing'), 'test_data', 'reports', stamp)
        # 远端报告文件可能带有 -quick 后缀
        md_candidates = [
            os.path.join(base_dir, f'storage_performance_report_{stamp}-quick.md'),
            os.path.join(base_dir, f'storage_performance_report_{stamp}.md'),
        ]
        remote_json = os.path.join(base_dir, 'report.json')

        md_ok = False
        for remote_md in md_candidates:
            r1 = scp_pull(host, user, auth, remote_md, os.path.join(raw_dir, f'{host}.md'))
            if r1.returncode == 0:
                md_ok = True
                break
        if not md_ok:
            errors.append((host, 'md', 'not found quick or normal md'))

        r2 = scp_pull(host, user, auth, remote_json, os.path.join(raw_dir, f'{host}.json'))
        if r2.returncode != 0:
            errors.append((host, 'json', r2.stderr.strip()))

    if errors:
        print('[WARN] 以下文件归集失败：')
        for h, t, e in errors:
            print(f' - {h} ({t}): {e}')
    else:
        print(f'[OK] 归集完成: {raw_dir}')


if __name__ == '__main__':
    main()
