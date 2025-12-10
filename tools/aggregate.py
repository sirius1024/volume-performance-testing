#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
from typing import Dict, List

import json as _json

# 添加项目根目录到 sys.path 以便导入 config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_cluster_config


def aggregate_cases(files: List[str]) -> Dict:
    agg: Dict[str, Dict] = {}
    count: Dict[str, int] = {}
    for fp in files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
        for c in data.get('cases', []):
            name = c.get('name')
            if not name:
                continue
            if name not in agg:
                agg[name] = {
                    'read': {'iops': 0.0, 'bw_MBps': 0.0, 'lat_us_sum': 0.0},
                    'write': {'iops': 0.0, 'bw_MBps': 0.0, 'lat_us_sum': 0.0},
                }
                count[name] = {'read': 0, 'write': 0}
            r = c.get('read', {})
            w = c.get('write', {})
            agg[name]['read']['iops'] += float(r.get('iops', 0.0))
            agg[name]['read']['bw_MBps'] += float(r.get('bw_MBps', 0.0))
            if 'lat_us' in r:
                agg[name]['read']['lat_us_sum'] += float(r.get('lat_us', 0.0))
                count[name]['read'] += 1
            agg[name]['write']['iops'] += float(w.get('iops', 0.0))
            agg[name]['write']['bw_MBps'] += float(w.get('bw_MBps', 0.0))
            if 'lat_us' in w:
                agg[name]['write']['lat_us_sum'] += float(w.get('lat_us', 0.0))
                count[name]['write'] += 1
    # finalize average
    cases = []
    for name, v in agg.items():
        rc = count[name]['read'] or 1
        wc = count[name]['write'] or 1
        cases.append({
            'name': name,
            'read': {
                'iops': v['read']['iops'],
                'bw_MBps': v['read']['bw_MBps'],
                'lat_us': v['read']['lat_us_sum'] / rc,
            },
            'write': {
                'iops': v['write']['iops'],
                'bw_MBps': v['write']['bw_MBps'],
                'lat_us': v['write']['lat_us_sum'] / wc,
            },
        })
    return {'cases': sorted(cases, key=lambda x: x['name'])}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='合并聚合 JSON 报告')
    parser.add_argument('--config', default='config/cluster.json')
    args = parser.parse_args()

    cfg = load_cluster_config(args.config)
    from datetime import datetime
    dt = datetime.strptime(cfg['start_time_utc'], '%Y-%m-%d %H:%M')
    stamp = dt.strftime('%Y%m%d-%H%M')

    centralized = os.path.join('test_data', 'reports', 'centralized', stamp)
    raw_dir = os.path.join(centralized, 'raw')
    files = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith('.json')]

    agg = aggregate_cases(files)
    meta = {
        'p': cfg.get('p', 3),
        'vm_count': len(files),
        'timestamp': stamp,
        'sources': [os.path.splitext(os.path.basename(f))[0] for f in files],
    }
    out = {'meta': meta, 'cases': agg['cases']}

    os.makedirs(centralized, exist_ok=True)
    json_path = os.path.join(centralized, 'aggregate.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    md_path = os.path.join(centralized, 'aggregate.md')
    lines = []
    lines.append('# 聚合存储性能报告\n')
    lines.append(f'生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
    lines.append('## 元信息\n')
    lines.append(f"- 物理机数(p): {out['meta']['p']}\n")
    lines.append(f"- 虚拟机数: {out['meta']['vm_count']}\n")
    lines.append(f"- 时间戳: {out['meta']['timestamp']}\n")
    lines.append(f"- 来源: {', '.join(out['meta']['sources'])}\n\n")
    lines.append('## 聚合案例\n\n')
    lines.append('| 名称 | 读IOPS | 写IOPS | 读MB/s | 写MB/s | 读延迟(μs) | 写延迟(μs) |\n')
    lines.append('|------|--------|--------|--------|--------|-------------|-------------|\n')
    for c in out['cases']:
        lines.append(
            f"| {c['name']} | "
            f"{c['read']['iops']:.0f} | {c['write']['iops']:.0f} | "
            f"{c['read']['bw_MBps']:.2f} | {c['write']['bw_MBps']:.2f} | "
            f"{c['read']['lat_us']:.1f} | {c['write']['lat_us']:.1f} |\n"
        )
    with open(md_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(json_path)
    print(md_path)


if __name__ == '__main__':
    main()
