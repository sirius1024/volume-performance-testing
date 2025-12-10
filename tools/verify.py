#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess
from datetime import datetime

# 添加项目根目录到 sys.path 以便导入 config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_cluster_config


def stamp_from_start(start: str) -> str:
    dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
    return dt.strftime('%Y%m%d-%H%M')


def run_remote(host: str, user: str, auth: dict, cmd: str):
    if auth.get('type') == 'key':
        key = os.path.expanduser(auth.get('value'))
        base = ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', f'{user}@{host}', cmd]
    else:
        pwd = auth.get('value')
        base = ['sshpass', '-p', pwd, 'ssh', '-o', 'StrictHostKeyChecking=no', f'{user}@{host}', cmd]
    return subprocess.run(base, capture_output=True, text=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='远端验证分钟目录与日志')
    parser.add_argument('--stamp')
    parser.add_argument('--config', default='config/cluster.json')
    args = parser.parse_args()

    cfg = load_cluster_config(args.config)
    stamp = args.stamp or stamp_from_start(cfg['start_time_utc'])
    workdir = cfg.get('remote_workdir', '/data/volume-performance-testing')
    base = os.path.join(workdir, 'test_data', 'reports', stamp)

    print(f'[VERIFY] stamp={stamp} base={base}')
    for vm in cfg['vms']:
        host = vm['host']; user = vm['user']; auth = vm['auth']
        print(f'--- {host} ---')
        cmds = [
            f'bash -lc "date -u +%s"',
            f'bash -lc "ls -ld {workdir} || echo MISSING_WORKDIR"',
            f'bash -lc "ls -l {workdir}/main.py || echo MISSING_MAIN"',
            f'bash -lc "python3 --version || echo PY_MISSING"',
            f'bash -lc "fio --version || echo FIO_MISSING"',
            f'bash -lc "sudo -n true && echo SUDO_NOPASS || echo SUDO_NEED_PASS"',
            f'bash -lc "sudo -E mkdir -p {base} && echo MKDIR_OK || echo MKDIR_FAIL"',
            f'bash -lc "echo VERIFY_WRITE | sudo -E tee -a {base}/run.log >/dev/null && echo WRITE_OK || echo WRITE_FAIL"',
            f'bash -lc "sudo -E tail -n 80 {base}/run.log 2>/dev/null || echo NO_RUNLOG"',
            f'bash -lc "tail -n 50 /tmp/volume-test-error.log 2>/dev/null || echo NO_ERRLOG"',
            f'bash -lc "ps aux | grep \"python3 -u main.py\" | grep -v grep || echo NO_PROCESS"',
        ]
        for c in cmds:
            r = run_remote(host, user, auth, c)
            sys.stdout.write(r.stdout)
            if r.returncode != 0:
                sys.stderr.write(r.stderr)


if __name__ == '__main__':
    main()
