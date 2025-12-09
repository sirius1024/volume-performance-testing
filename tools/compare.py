#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json


def load(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_cases(a: dict, b: dict) -> list:
    amap = {c['name']: c for c in a.get('cases', [])}
    bmap = {c['name']: c for c in b.get('cases', [])}
    names = sorted(set(amap.keys()) & set(bmap.keys()))
    out = []
    for n in names:
        ca = amap[n]; cb = bmap[n]
        def metric(baseline, current):
            delta = current - baseline
            pct = (delta / baseline * 100.0) if baseline else 0.0
            return {'baseline': baseline, 'current': current, 'delta': delta, 'delta_pct': pct}
        item = {'name': n}
        item['read_iops'] = metric(ca['read']['iops'], cb['read']['iops'])
        item['write_iops'] = metric(ca['write']['iops'], cb['write']['iops'])
        item['read_bw'] = metric(ca['read']['bw_MBps'], cb['read']['bw_MBps'])
        item['write_bw'] = metric(ca['write']['bw_MBps'], cb['write']['bw_MBps'])
        # 延迟越小越好：附加趋势
        rl = metric(ca['read']['lat_us'], cb['read']['lat_us'])
        wl = metric(ca['write']['lat_us'], cb['write']['lat_us'])
        rl['trend'] = 'improved' if rl['delta'] < 0 else ('declined' if rl['delta'] > 0 else 'flat')
        wl['trend'] = 'improved' if wl['delta'] < 0 else ('declined' if wl['delta'] > 0 else 'flat')
        item['read_lat_us'] = rl
        item['write_lat_us'] = wl
        out.append(item)
    return out


def auto_pick(base_dir: str) -> tuple[str, str]:
    stamps = sorted([d for d in os.listdir(base_dir) if d[:8].isdigit() and '-' in d])
    if len(stamps) < 2:
        raise RuntimeError('不足两份聚合报告用于自动对比')
    return stamps[-2], stamps[-1]


def main():
    import argparse
    parser = argparse.ArgumentParser(description='对比两份聚合 JSON')
    parser.add_argument('--baseline')
    parser.add_argument('--current')
    parser.add_argument('--auto', action='store_true')
    args = parser.parse_args()

    base_dir = os.path.join('test_data', 'reports', 'centralized')
    if args.auto:
        b, c = auto_pick(base_dir)
    else:
        if not args.baseline or not args.current:
            raise SystemExit('需要提供 --baseline 与 --current 或使用 --auto')
        b, c = args.baseline, args.current

    a_path = os.path.join(base_dir, b, 'aggregate.json')
    b_path = os.path.join(base_dir, c, 'aggregate.json')
    A = load(a_path); B = load(b_path)

    # 同类型约束：p 相同
    pa = A.get('meta', {}).get('p'); pb = B.get('meta', {}).get('p')
    if pa != pb:
        raise SystemExit(f'不支持不同 p 的对比: {pa} vs {pb}')

    items = compare_cases(A, B)
    out_dir = os.path.join(base_dir, 'compare')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{b}_vs_{c}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'baseline': b, 'current': c, 'p': pa, 'items': items}, f, ensure_ascii=False, indent=2)
    print(out_path)


if __name__ == '__main__':
    main()

