#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fio_test import FIOTestRunner
from dd_test import DDTestRunner
from common import Logger, ensure_directory


def build_fio_commands(test_dir: str, runtime: int) -> List[str]:
    logger = Logger(os.path.join(test_dir, "dump_commands.log"))
    fio = FIOTestRunner(test_dir, logger, runtime)

    commands = []
    for block_size in fio.block_sizes:
        for queue_depth in fio.queue_depths:
            for numjobs in fio.iodepth_numjobs_mapping[queue_depth]:
                for rwmix_read in fio.rwmix_ratios:
                    if rwmix_read == 0:
                        test_type = "randwrite"
                    elif rwmix_read == 100:
                        test_type = "randread"
                    else:
                        test_type = "randrw"

                    filename = f"fio_test_{block_size}_{queue_depth}_{numjobs}_{rwmix_read}"
                    cmd = [
                        "fio",
                        "--name=test",
                        f"--filename={filename}",
                        f"--rw={test_type}",
                        f"--bs={block_size}",
                        f"--iodepth={queue_depth}",
                        f"--numjobs={numjobs}",
                        f"--runtime={runtime}",
                        "--time_based",
                        "--direct=1",
                        "--ioengine=libaio",
                        "--group_reporting",
                        "--output-format=json",
                        "--size=10G",
                    ]
                    if test_type == "randrw":
                        cmd.append(f"--rwmixread={rwmix_read}")
                    commands.append(" ".join(cmd))
    return commands


def build_dd_commands(test_dir: str) -> List[str]:
    # Mirror dd_test.py configurations
    commands = []
    # 顺序写入测试
    write_configs = [
        ("1G", "1G", 1),
        ("1G", "4G", 4),
        ("1M", "1G", 1024),
        ("64K", "1G", 16384),
        ("32K", "1G", 32768),
    ]
    for block_size, file_size, count in write_configs:
        test_file = f"testfile_write_{block_size.lower()}"
        cmd = [
            "dd",
            "if=/dev/zero",
            f"of={test_file}",
            f"bs={block_size}",
            f"count={count}",
            "oflag=direct",
        ]
        commands.append(" ".join(cmd))

    # 带同步选项的顺序写入测试
    sync_write_configs = [
        ("1M", "1G", 1024, "direct,dsync"),
        ("64K", "1G", 16384, "direct,dsync"),
        ("32K", "1G", 32768, "direct,dsync"),
        ("1M", "1G", 1024, "dsync"),
        ("64K", "1G", 16384, "dsync"),
        ("32K", "1G", 32768, "dsync"),
    ]
    for block_size, file_size, count, oflag in sync_write_configs:
        test_file = f"testfile_write_{block_size.lower()}_{oflag.replace(',', '_')}"
        cmd = [
            "dd",
            "if=/dev/zero",
            f"of={test_file}",
            f"bs={block_size}",
            f"count={count}",
            f"oflag={oflag}",
        ]
        commands.append(" ".join(cmd))

    # 顺序读取测试（列出命令，假定预写入文件存在）
    read_configs = [
        ("1G", "1G", 1, "testfile_write_1g"),
        ("1G", "4G", 4, "testfile_write_1g"),
        ("1M", "1G", 1024, "testfile_write_1m"),
        ("64K", "1G", 16384, "testfile_write_64k"),
        ("32K", "1G", 32768, "testfile_write_32k"),
    ]
    for block_size, file_size, count, input_file in read_configs:
        cmd = [
            "dd",
            f"if={input_file}",
            "of=/dev/null",
            f"bs={block_size}",
            f"count={count}",
            "iflag=direct",
        ]
        commands.append(" ".join(cmd))

    return commands


def main():
    test_dir = "./test_data"
    ensure_directory(test_dir)

    ts = time.strftime('%Y%m%d_%H%M%S')
    reports_dir = os.path.join(test_dir, "reports", ts)
    ensure_directory(reports_dir)
    out_path = os.path.join(reports_dir, "commands_manifest.md")

    fio_cmds = build_fio_commands(test_dir, runtime=3)
    dd_cmds = build_dd_commands(test_dir)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 全量测试命令清单\n\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"测试目录 (cwd): {os.path.abspath(test_dir)}\n\n")

        f.write(f"## FIO 命令（{len(fio_cmds)} 条，size=10G）\n\n")
        for i, cmd in enumerate(fio_cmds, 1):
            f.write(f"{i}. `{cmd}`\n")

        f.write("\n## DD 命令\n\n")
        for i, cmd in enumerate(dd_cmds, 1):
            f.write(f"{i}. `{cmd}`\n")

    print(out_path)


if __name__ == "__main__":
    main()
