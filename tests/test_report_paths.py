import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import StoragePerformanceTest
from models.result import TestResult
from utils.file_utils import ensure_directory

def make_dummy_fio_results():
    r = TestResult(test_name="dummy_fio", test_type="fio")
    r.read_iops = 100
    r.write_iops = 0
    r.read_mbps = 50.0
    r.read_latency_us = 100.0
    return [r]

def run():
    test_dir = "./test_data"
    ensure_directory(test_dir)
    t = StoragePerformanceTest(test_dir, runtime=1)
    t.fio_runner.run_quick_fio_tests = make_dummy_fio_results
    dd_results, fio_results = t.run_all_tests(include_dd=False, include_fio=True, quick_mode=True)
    report_path = t.generate_report(dd_results, fio_results, None)
    ts = t.run_timestamp
    reports_dir = os.path.join(test_dir, "reports", ts)
    assert os.path.isdir(reports_dir)
    assert report_path.endswith("-quick.md")
    assert os.path.dirname(report_path) == reports_dir
    fio_detail = os.path.join(reports_dir, "fio_detailed_report-quick.md")
    assert os.path.isfile(fio_detail)
    custom = os.path.join(test_dir, "custom.md")
    custom_out = t.generate_report([], [], custom)
    assert custom_out == os.path.join(test_dir, "custom-quick.md")
    print("REPORT_DIR:", reports_dir)
    print("MAIN_REPORT:", report_path)
    print("FIO_REPORT:", fio_detail)
    print("CUSTOM_REPORT:", custom_out)
    print("OK")

if __name__ == "__main__":
    run()
