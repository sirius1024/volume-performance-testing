#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fio_test import FIOTestRunner
from utils.logger import Logger

def main():
    runner = FIOTestRunner(test_dir="./test_data", logger=Logger("./test_data/check.log"), runtime=3)
    violations = []
    for bs in runner.block_sizes:
        for qd in runner.queue_depths:
            for nj in runner.iodepth_numjobs_mapping[qd]:
                prod = qd * nj
                if prod > 256:
                    violations.append((bs, qd, nj, prod))
    if violations:
        print("FOUND violations where iodepth*numjobs > 256:")
        for bs, qd, nj, prod in violations:
            print(f"bs={bs} qd={qd} nj={nj} product={prod}")
        return 1
    else:
        print("OK: no product exceeds 256")
        return 0

if __name__ == "__main__":
    exit(main())

