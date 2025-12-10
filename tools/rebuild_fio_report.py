#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import StoragePerformanceTest


def main():
    test_dir = os.environ.get("TEST_DIR", "./test_data")
    stamp = os.environ.get("STAMP")
    rpt = StoragePerformanceTest(test_dir, runtime=3)
    if stamp:
        rpt.run_timestamp = stamp
    rpt.quick_mode = True
    fio_results = rpt.run_fio_tests(quick_mode=True)
    print(f"生成: {os.path.join(test_dir, 'reports', rpt.run_timestamp or 'unknown')}")


if __name__ == "__main__":
    main()

