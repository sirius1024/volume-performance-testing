#!/usr/bin/env python3
import os
import sys
import argparse
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fio_test import FIOTestRunner
from common import TestResult, Logger


def verify_file(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    jobs = data.get("jobs", [])
    job = jobs[0] if jobs else {}
    opts = job.get("job options", {})
    rw = str(opts.get("rw", "randread")).lower()
    bs = str(opts.get("bs", "4k")).lower()
    iodepth = int(str(opts.get("iodepth", "1")))
    numjobs = int(str(opts.get("numjobs", "1")))
    rwmix = 0
    if rw == "randrw":
        rwmix = int(str(opts.get("rwmixread", "50")))
    elif rw == "randread":
        rwmix = 100
    else:
        rwmix = 0
    logger = Logger()
    runner = FIOTestRunner(test_dir=".", logger=logger)
    result = TestResult(
        test_name=f"VERIFY {rw}",
        test_type=rw,
        block_size=bs,
        queue_depth=iodepth,
        numjobs=numjobs,
        rwmix_read=rwmix,
    )
    with open(json_path, "r", encoding="utf-8") as f:
        runner._parse_fio_json_output(f.read(), result)
    out = []
    out.append(f"case: {os.path.basename(json_path)} -> type={rw}, rwmix_read={rwmix}")
    out.append(f"  read_iops={result.read_iops:.0f}, write_iops={result.write_iops:.0f}")
    out.append(f"  read_mbps={result.read_mbps:.2f}, write_mbps={result.write_mbps:.2f}")
    out.append(f"  read_lat_us={result.read_latency_us:.2f}, write_lat_us={result.write_latency_us:.2f}")
    print("\n".join(out))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="test_data")
    parser.add_argument("--paths", nargs="*")
    args = parser.parse_args()
    files = args.paths if args.paths else []
    if not files:
        for name in os.listdir(args.dir):
            if name.startswith("fio_json_") and name.endswith(".json"):
                files.append(os.path.join(args.dir, name))
    if not files:
        print("no json files found")
        return
    for fp in sorted(files):
        if os.path.isfile(fp):
            verify_file(fp)
        else:
            print("missing:", fp)


if __name__ == "__main__":
    main()
