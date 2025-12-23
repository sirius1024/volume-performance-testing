#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json

# 添加项目根目录到 sys.path 以便导入 config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_cluster_config


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
            pct = (delta / baseline * 100.0) if baseline not in (0, 0.0) else None
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


def _to_float(s: str) -> float:
    try:
        return float(s.strip())
    except Exception:
        return 0.0


def parse_md_cases(md_path: str) -> dict:
    if not os.path.isfile(md_path):
        return {'cases': []}
    with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    cases = []
    header_idx = -1
    for i, l in enumerate(lines):
        if l.strip().startswith('|') and ('名称' in l or '读写模式' in l):
            header_idx = i
            break
    if header_idx == -1:
        return {'cases': []}
    header_cells = [c.strip() for c in lines[header_idx].split('|')]
    col_map = {name: idx for idx, name in enumerate(header_cells) if name}
    sep_idx = header_idx + 1
    for j in range(sep_idx + 1, len(lines)):
        row = lines[j].strip()
        if not row.startswith('|'):
            break
        cells = [c.strip() for c in row.split('|')]
        if len(cells) < len(header_cells):
            continue
        if '名称' in col_map:
            name = cells[col_map['名称']]
            riops = _to_float(cells[col_map.get('读IOPS','') or 0])
            wiops = _to_float(cells[col_map.get('写IOPS','') or 0])
            rmbps = _to_float(cells[col_map.get('读MB/s','') or 0])
            wmbps = _to_float(cells[col_map.get('写MB/s','') or 0])
            rlat = _to_float(cells[col_map.get('读延迟(μs)','') or 0])
            wlat = _to_float(cells[col_map.get('写延迟(μs)','') or 0])
        else:
            mode = cells[col_map.get('读写模式', 0)]
            qd = cells[col_map.get('队列深度', 0)]
            nj = cells[col_map.get('并发数', 0)]
            name = f"{mode} QD{qd} J{nj}"
            riops = _to_float(cells[col_map.get('读取IOPS','') or 0])
            wiops = _to_float(cells[col_map.get('写入IOPS','') or 0])
            rmbps = _to_float(cells[col_map.get('读取带宽(MB/s)','') or 0])
            wmbps = _to_float(cells[col_map.get('写入带宽(MB/s)','') or 0])
            rlat = _to_float(cells[col_map.get('读取延迟(μs)','') or 0])
            wlat = _to_float(cells[col_map.get('写入延迟(μs)','') or 0])
        cases.append({
            'name': name,
            'read': {'iops': riops, 'bw_MBps': rmbps, 'lat_us': rlat},
            'write': {'iops': wiops, 'bw_MBps': wmbps, 'lat_us': wlat},
        })
    return {'cases': cases}


def auto_pick(base_dir: str) -> tuple[str, str]:
    candidates = []
    for d in os.listdir(base_dir):
        if d[:8].isdigit() and '-' in d:
            agg_path = os.path.join(base_dir, d, 'aggregate.json')
            if os.path.isfile(agg_path):
                candidates.append(d)
    stamps = sorted(candidates)
    if len(stamps) < 2:
        raise RuntimeError('不足两份聚合报告用于自动对比')
    return stamps[-2], stamps[-1]


def write_md(out_path: str, title: str, meta: dict, items: list):
    lines = []
    lines.append(f"# {title}\n")
    lines.append(f"生成时间: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("## 元信息\n")
    for k, v in meta.items():
        lines.append(f"- {k}: {v}\n")
    # 摘要统计
    improved = {'read_iops':0,'write_iops':0,'read_bw':0,'write_bw':0,'read_lat_us':0,'write_lat_us':0}
    declined = {'read_iops':0,'write_iops':0,'read_bw':0,'write_bw':0,'read_lat_us':0,'write_lat_us':0}
    for it in items:
        ri = it['read_iops']; wi = it['write_iops']; rb = it['read_bw']; wb = it['write_bw']; rl = it['read_lat_us']; wl = it['write_lat_us']
        if ri['delta']>0: improved['read_iops']+=1
        elif ri['delta']<0: declined['read_iops']+=1
        if wi['delta']>0: improved['write_iops']+=1
        elif wi['delta']<0: declined['write_iops']+=1
        if rb['delta']>0: improved['read_bw']+=1
        elif rb['delta']<0: declined['read_bw']+=1
        if wb['delta']>0: improved['write_bw']+=1
        elif wb['delta']<0: declined['write_bw']+=1
        if rl['delta']<0: improved['read_lat_us']+=1
        elif rl['delta']>0: declined['read_lat_us']+=1
        if wl['delta']<0: improved['write_lat_us']+=1
        elif wl['delta']>0: declined['write_lat_us']+=1
    lines.append("\n## 摘要\n\n")
    lines.append(
        f"- 读IOPS: 📈{improved['read_iops']} / 📉{declined['read_iops']}\n"
        f"- 写IOPS: 📈{improved['write_iops']} / 📉{declined['write_iops']}\n"
        f"- 读MB/s: 📈{improved['read_bw']} / 📉{declined['read_bw']}\n"
        f"- 写MB/s: 📈{improved['write_bw']} / 📉{declined['write_bw']}\n"
        f"- 读延迟(μs): ✅改善 {improved['read_lat_us']} / ❌变差 {declined['read_lat_us']}\n"
        f"- 写延迟(μs): ✅改善 {improved['write_lat_us']} / ❌变差 {declined['write_lat_us']}\n"
    )
    # Top变化
    def top_list(metric_key: str, asc: bool, limit: int = 5):
        arr = []
        for it in items:
            m = it[metric_key]['delta']
            arr.append((it['name'], m))
        arr.sort(key=lambda x: x[1], reverse=not asc)
        return arr[:limit]
    tops = {
        '读IOPS↑': top_list('read_iops', asc=False),
        '读IOPS↓': top_list('read_iops', asc=True),
        '写IOPS↑': top_list('write_iops', asc=False),
        '写IOPS↓': top_list('write_iops', asc=True),
        '读MB/s↑': top_list('read_bw', asc=False),
        '读MB/s↓': top_list('read_bw', asc=True),
        '写MB/s↑': top_list('write_bw', asc=False),
        '写MB/s↓': top_list('write_bw', asc=True),
    }
    lines.append("\n## Top变化\n\n")
    for k, arr in tops.items():
        lines.append(f"- {k}: ")
        if not arr:
            lines.append("无\n")
        else:
            lines.append(", ".join([f"{name} ({delta:+.2f})" for name, delta in arr]) + "\n")

    lines.append("\n## 指标变化\n\n")
    lines.append("| 名称 | 读IOPSΔ | 读IOPS% | 写IOPSΔ | 写IOPS% | 读MB/sΔ | 读MB/s% | 写MB/sΔ | 写MB/s% | 读延迟Δ(μs) | 写延迟Δ(μs) | 读趋势 | 写趋势 |\n")
    lines.append("|------|---------:|--------:|---------:|--------:|--------:|--------:|--------:|--------:|-----------:|-----------:|--------|--------|\n")
    for it in items:
        ri = it['read_iops']; wi = it['write_iops']; rb = it['read_bw']; wb = it['write_bw']; rl = it['read_lat_us']; wl = it['write_lat_us']
        def fmt_pct(x):
            return f"{x:.2f}%" if x is not None else "-"
        def emoj(t):
            return '📈' if t=='improved' else ('📉' if t=='declined' else '➖')
        lines.append(
            f"| {it['name']} | "
            f"{ri['delta']:.2f} | {fmt_pct(ri['delta_pct'])} | "
            f"{wi['delta']:.2f} | {fmt_pct(wi['delta_pct'])} | "
            f"{rb['delta']:.2f} | {fmt_pct(rb['delta_pct'])} | "
            f"{wb['delta']:.2f} | {fmt_pct(wb['delta_pct'])} | "
            f"{rl['delta']:.2f} | {wl['delta']:.2f} | "
            f"{emoj(rl.get('trend','flat'))} | {emoj(wl.get('trend','flat'))} |\n"
        )
    with open(out_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='对比两份报告')
    parser.add_argument('--baseline')
    parser.add_argument('--current')
    parser.add_argument('--auto', action='store_true')
    parser.add_argument('--source', choices=['centralized', 'raw', 'auto'], default='auto')
    parser.add_argument('--host')
    parser.add_argument('--dirA')
    parser.add_argument('--dirB')
    args = parser.parse_args()

    # 优先支持按目录指定：用户给两个文件夹即可
    if args.dirA and args.dirB:
        a_dir = args.dirA
        b_dir = args.dirB
        a_agg = os.path.isfile(os.path.join(a_dir, 'aggregate.json'))
        b_agg = os.path.isfile(os.path.join(b_dir, 'aggregate.json'))
        def has_single(d: str) -> bool:
            if os.path.isfile(os.path.join(d, 'report.json')):
                return True
            # 存在主综合报告MD
            for f in os.listdir(d):
                if f.startswith('storage_performance_report_') and f.endswith('.md'):
                    return True
                if f.startswith('fio_detailed_report') and f.endswith('.md'):
                    return True
            return False
        a_single = has_single(a_dir)
        b_single = has_single(b_dir)
        if a_agg and b_agg:
            # 聚合对比（3pNv）
            A = load(os.path.join(a_dir, 'aggregate.json'))
            B = load(os.path.join(b_dir, 'aggregate.json'))
            pa = A.get('meta', {}).get('p'); pb = B.get('meta', {}).get('p')
            va = A.get('meta', {}).get('vm_count'); vb = B.get('meta', {}).get('vm_count')
            if pa != pb or va != vb:
                raise SystemExit(f'不支持不同类型的对比: p={pa} vs {pb}, vm_count={va} vs {vb}')
            items = compare_cases(A, B)
            out_dir = os.path.join('test_data', 'reports', 'compare')
            os.makedirs(out_dir, exist_ok=True)
            bname = f"{os.path.basename(a_dir)}_vs_{os.path.basename(b_dir)}"
            out_json = os.path.join(out_dir, f'{bname}.json')
            with open(out_json, 'w', encoding='utf-8') as f:
                json.dump({'baseline': os.path.basename(a_dir), 'current': os.path.basename(b_dir), 'p': pa, 'vm_count': va, 'items': items}, f, ensure_ascii=False, indent=2)
            out_md = os.path.join(out_dir, f'{bname}.md')
            meta = {'类型': '集中聚合(3pNv)', 'p': pa, 'vm_count': va, 'baseline': os.path.basename(a_dir), 'current': os.path.basename(b_dir)}
            write_md(out_md, '聚合报告对比', meta, items)
            print(out_json); print(out_md); return
        elif a_single and b_single:
            # 单机报告对比（reports/<stamp>/report.json 或解析MD）
            a_json = os.path.join(a_dir, 'report.json')
            b_json = os.path.join(b_dir, 'report.json')
            A = load(a_json) if os.path.isfile(a_json) else {'cases': []}
            B = load(b_json) if os.path.isfile(b_json) else {'cases': []}
            if not A.get('cases'):
                # 尝试解析 MD（优先主综合，其次详细报告）
                mdA = next((os.path.join(a_dir, f) for f in os.listdir(a_dir) if f.startswith('storage_performance_report_') and f.endswith('.md')), None)
                if not mdA:
                    mdA = next((os.path.join(a_dir, f) for f in os.listdir(a_dir) if f.startswith('fio_detailed_report') and f.endswith('.md')), None)
                A = parse_md_cases(mdA or '')
            if not B.get('cases'):
                mdB = next((os.path.join(b_dir, f) for f in os.listdir(b_dir) if f.startswith('storage_performance_report_') and f.endswith('.md')), None)
                if not mdB:
                    mdB = next((os.path.join(b_dir, f) for f in os.listdir(b_dir) if f.startswith('fio_detailed_report') and f.endswith('.md')), None)
                B = parse_md_cases(mdB or '')
            items = compare_cases({'cases': A.get('cases', [])}, {'cases': B.get('cases', [])})
            out_dir = os.path.join('test_data', 'reports', 'compare')
            os.makedirs(out_dir, exist_ok=True)
            bname = f"{os.path.basename(a_dir)}_vs_{os.path.basename(b_dir)}"
            out_json = os.path.join(out_dir, f'{bname}.json')
            with open(out_json, 'w', encoding='utf-8') as f:
                json.dump({'baseline': os.path.basename(a_dir), 'current': os.path.basename(b_dir), 'items': items}, f, ensure_ascii=False, indent=2)
            out_md = os.path.join(out_dir, f'{bname}.md')
            meta = {'类型': '单机报告', 'baseline': os.path.basename(a_dir), 'current': os.path.basename(b_dir)}
            write_md(out_md, '单机报告对比', meta, items)
            print(out_json); print(out_md); return
        else:
            raise SystemExit('目录对比失败：请提供 centralized/<stamp>/（含 aggregate.json）或 reports/<stamp>/（含 report.json 或 storage_performance_report_*.md）')

    # 兼容旧参数：centralized/raw 模式
    if args.source == 'centralized':
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
        pa = A.get('meta', {}).get('p'); pb = B.get('meta', {}).get('p')
        va = A.get('meta', {}).get('vm_count'); vb = B.get('meta', {}).get('vm_count')
        if pa != pb or va != vb:
            raise SystemExit(f'不支持不同类型的对比: p={pa} vs {pb}, vm_count={va} vs {vb}')
        items = compare_cases(A, B)
        out_dir = os.path.join('test_data', 'reports', 'compare')
        os.makedirs(out_dir, exist_ok=True)
        out_json = os.path.join(out_dir, f'{b}_vs_{c}.json')
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump({'baseline': b, 'current': c, 'p': pa, 'vm_count': va, 'items': items}, f, ensure_ascii=False, indent=2)
        out_md = os.path.join(out_dir, f'{b}_vs_{c}.md')
        meta = {'类型': '集中聚合(3pNv)', 'p': pa, 'vm_count': va, 'baseline': b, 'current': c}
        write_md(out_md, '聚合报告对比', meta, items)
        print(out_json)
        print(out_md)
    elif args.source == 'raw':
        base_dir = os.path.join('test_data', 'reports', 'centralized')
        if not args.host:
            raise SystemExit('raw 对比需要提供 --host')
        if not args.baseline or not args.current:
            raise SystemExit('需要提供 --baseline 与 --current')
        b, c = args.baseline, args.current
        a_path = os.path.join(base_dir, b, 'raw', f'{args.host}.json')
        b_path = os.path.join(base_dir, c, 'raw', f'{args.host}.json')
        if not os.path.isfile(a_path) or not os.path.isfile(b_path):
            raise SystemExit('未找到指定主机的原始JSON')
        A = load(a_path); B = load(b_path)
        items = compare_cases({'cases': A.get('cases', [])}, {'cases': B.get('cases', [])})
        out_dir = os.path.join('test_data', 'reports', 'compare')
        os.makedirs(out_dir, exist_ok=True)
        out_json = os.path.join(out_dir, f'{b}_vs_{c}_{args.host}.json')
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump({'baseline': b, 'current': c, 'host': args.host, 'items': items}, f, ensure_ascii=False, indent=2)
        out_md = os.path.join(out_dir, f'{b}_vs_{c}_{args.host}.md')
        meta = {'类型': '单机(raw)', 'host': args.host, 'baseline': b, 'current': c}
        write_md(out_md, '单机报告对比', meta, items)
        print(out_json)
        print(out_md)
    else:
        raise SystemExit('请使用 --dirA/--dirB 指定两个文件夹，或 --source centralized/raw 旧模式')


if __name__ == '__main__':
    main()
def _to_float(s: str) -> float:
    try:
        return float(s.strip())
    except Exception:
        return 0.0


def parse_md_cases(md_path: str) -> dict:
    if not os.path.isfile(md_path):
        return {'cases': []}
    with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    cases = []
    header_idx = -1
    for i, l in enumerate(lines):
        if l.strip().startswith('|') and ('名称' in l or '读写模式' in l):
            header_idx = i
            break
    if header_idx == -1:
        return {'cases': []}
    # build column index map
    header_cells = [c.strip() for c in lines[header_idx].split('|')]
    col_map = {name: idx for idx, name in enumerate(header_cells) if name}
    sep_idx = header_idx + 1
    for j in range(sep_idx + 1, len(lines)):
        row = lines[j].strip()
        if not row.startswith('|'):
            break
        cells = [c.strip() for c in row.split('|')]
        if len(cells) < len(header_cells):
            continue
        if '名称' in col_map:
            name = cells[col_map['名称']]
            riops = _to_float(cells[col_map.get('读IOPS','') or 0])
            wiops = _to_float(cells[col_map.get('写IOPS','') or 0])
            rmbps = _to_float(cells[col_map.get('读MB/s','') or 0])
            wmbps = _to_float(cells[col_map.get('写MB/s','') or 0])
            rlat = _to_float(cells[col_map.get('读延迟(μs)','') or 0])
            wlat = _to_float(cells[col_map.get('写延迟(μs)','') or 0])
        else:
            # 详细报告
            mode = cells[col_map.get('读写模式', 0)]
            qd = cells[col_map.get('队列深度', 0)]
            nj = cells[col_map.get('并发数', 0)]
            name = f"{mode} QD{qd} J{nj}"
            riops = _to_float(cells[col_map.get('读取IOPS','') or 0])
            wiops = _to_float(cells[col_map.get('写入IOPS','') or 0])
            rmbps = _to_float(cells[col_map.get('读取带宽(MB/s)','') or 0])
            wmbps = _to_float(cells[col_map.get('写入带宽(MB/s)','') or 0])
            rlat = _to_float(cells[col_map.get('读取延迟(μs)','') or 0])
            wlat = _to_float(cells[col_map.get('写入延迟(μs)','') or 0])
        cases.append({
            'name': name,
            'read': {'iops': riops, 'bw_MBps': rmbps, 'lat_us': rlat},
            'write': {'iops': wiops, 'bw_MBps': wmbps, 'lat_us': wlat},
        })
    return {'cases': cases}
