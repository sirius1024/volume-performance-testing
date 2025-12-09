#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from typing import Dict, List

import json as _json


def load_cluster(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return _json.load(f)


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

    cfg = load_cluster(args.config)
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
    with open(os.path.join(centralized, 'aggregate.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(os.path.join(centralized, 'aggregate.json'))


if __name__ == '__main__':
    main()
