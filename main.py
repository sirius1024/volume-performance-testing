#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储性能测试主控脚本
支持选择执行DD测试、FIO测试或两者同时执行
"""

import argparse
import os
import sys
import time
import json
from typing import List, Optional

from models.result import TestResult
from utils.logger import Logger
from utils.system_info import SystemInfoCollector
from utils.file_utils import ensure_directory
from dd_test import DDTestRunner
from fio_test import FIOTestRunner
from report_generator import ReportGenerator


class StoragePerformanceTest:
    """存储性能测试主类"""
    
    def __init__(self, test_dir: str, runtime: int = 3):
        self.test_dir = test_dir
        self.runtime = runtime
        self.run_timestamp = None
        self.quick_mode = False
        
        # 确保测试目录存在
        if not ensure_directory(test_dir):
            raise RuntimeError(f"无法创建测试目录: {test_dir}")
        
        # 创建日志记录器
        log_file = os.path.join(test_dir, "storage_test.log")
        self.logger = Logger(log_file)
        
        # 创建测试执行器
        self.dd_runner = DDTestRunner(test_dir, self.logger, core_file="config/core_scenarios.json")
        self.fio_runner = FIOTestRunner(test_dir, self.logger, runtime, core_file="config/core_scenarios.json")
        
        # 创建报告生成器
        self.report_generator = ReportGenerator(self.logger)
        
        # 创建系统信息收集器
        self.system_collector = SystemInfoCollector()
    
    def run_dd_tests(self, quick_mode: bool = False) -> List[TestResult]:
        """运行DD测试"""
        self.logger.info("=== 开始DD测试 ===")
        
        if quick_mode:
            return self.dd_runner.run_quick_dd_tests()
        else:
            return self.dd_runner.run_all_dd_tests()
    
    def run_fio_tests(self, quick_mode: bool = False) -> List[TestResult]:
        """运行FIO测试"""
        self.logger.info("=== 开始FIO测试 ===")
        
        if quick_mode:
            results = self.fio_runner.run_quick_fio_tests()
        else:
            results = self.fio_runner.run_comprehensive_fio_tests()
        
        # 生成详细报告
        if results:
            ts = self.run_timestamp or time.strftime('%Y%m%d-%H%M', time.gmtime())
            reports_dir = os.path.join(self.test_dir, "reports", ts)
            ensure_directory(reports_dir)
            name = "fio_detailed_report.md"
            if self.quick_mode:
                base, ext = os.path.splitext(name)
                name = f"{base}-quick{ext}"
            detailed_report_file = os.path.join(reports_dir, name)
            self.fio_runner.generate_detailed_report(results, detailed_report_file)
            self.logger.info(f"FIO详细报告已生成: {detailed_report_file}")
        
        return results
    
    def run_all_tests(self, include_dd: bool = True, include_fio: bool = True, 
                     quick_mode: bool = False) -> tuple[List[TestResult], List[TestResult]]:
        """运行所有测试"""
        dd_results = []
        fio_results = []
        core_results = []
        
        start_time = time.time()
        if not self.run_timestamp:
            self.run_timestamp = time.strftime('%Y%m%d-%H%M', time.gmtime())
        self.quick_mode = quick_mode
        
        try:
            if include_dd:
                dd_results = self.run_dd_tests(quick_mode)
            
            if include_fio:
                fio_results = self.run_fio_tests(quick_mode)
            
            total_time = time.time() - start_time
            self.logger.info(f"所有测试完成，总耗时: {total_time/60:.1f}分钟")
            
            return dd_results, fio_results
        
        except Exception as e:
            self.logger.error(f"测试过程中出现错误: {str(e)}")
            raise
    
    def generate_report(self, dd_results: List[TestResult], fio_results: List[TestResult], 
                       output_file: Optional[str] = None):
        """生成测试报告"""
        if output_file is None:
            ts = self.run_timestamp or time.strftime('%Y%m%d-%H%M', time.gmtime())
            reports_dir = os.path.join(self.test_dir, "reports", ts)
            ensure_directory(reports_dir)
            name = f"storage_performance_report_{ts}.md"
            if self.quick_mode:
                base, ext = os.path.splitext(name)
                name = f"{base}-quick{ext}"
            output_file = os.path.join(reports_dir, name)
        else:
            if self.quick_mode:
                dirn = os.path.dirname(output_file)
                base = os.path.basename(output_file)
                b, e = os.path.splitext(base)
                output_file = os.path.join(dirn, f"{b}-quick{e}")
        
        # 收集系统信息
        system_info = self.system_collector.collect_system_info()
        
        # 生成报告
        core_results = []
        # 聚合核心场景：取标记为"CORE "的结果，快速与完整模式均应包含
        core_results.extend([r for r in dd_results if r.test_name.startswith("CORE ")])
        core_results.extend([r for r in fio_results if r.test_name.startswith("CORE ")])
        self.report_generator.generate_report(dd_results, fio_results, output_file, system_info, core_results)
        dirn = os.path.dirname(output_file)
        report_json = os.path.join(dirn, "report.json")
        cases = []
        for r in fio_results:
            cases.append({
                "name": r.test_name,
                "read": {
                    "iops": r.read_iops,
                    "bw_MBps": r.read_mbps,
                    "lat_us": r.read_latency_us
                },
                "write": {
                    "iops": r.write_iops,
                    "bw_MBps": r.write_mbps,
                    "lat_us": r.write_latency_us
                }
            })
        try:
            with open(report_json, "w", encoding="utf-8") as f:
                json.dump({"cases": cases}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"JSON报告已生成: {report_json}")
        except Exception as e:
            self.logger.warning(f"写入JSON报告失败: {str(e)}")
        
        return output_file
    
    def cleanup(self):
        """清理测试文件"""
        self.logger.info("开始清理测试文件")
        self.dd_runner.cleanup_test_files()
        self.fio_runner.cleanup_test_files()
        self.logger.info("测试文件清理完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="存储性能测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --all                    # 运行所有测试
  python main.py --dd-only                # 仅运行DD测试
  python main.py --fio-only               # 仅运行FIO测试
  python main.py --fio-only --quick       # 运行FIO快速测试
  python main.py --all --runtime 10       # 运行所有测试，FIO每个测试10秒
  python main.py --fio-info               # 显示FIO测试矩阵信息
        """
    )
    
    # 测试类型选择
    test_group = parser.add_mutually_exclusive_group(required=False)
    test_group.add_argument("--all", action="store_true", help="运行所有测试（DD + FIO）")
    test_group.add_argument("--dd-only", action="store_true", help="仅运行DD测试")
    test_group.add_argument("--fio-only", action="store_true", help="仅运行FIO测试")
    test_group.add_argument("--fio-info", action="store_true", help="显示FIO测试矩阵信息")
    
    # 测试参数
    parser.add_argument("--test-dir", default="./test_data", help="测试目录路径（默认: ./test_data）")
    parser.add_argument("--runtime", type=int, default=3, help="FIO每个测试的运行时间，秒（默认: 3）")
    parser.add_argument("--quick", action="store_true", help="快速模式，仅运行代表性测试")
    parser.add_argument("--cleanup", action="store_true", help="测试完成后清理测试文件")
    parser.add_argument("--output", help="指定报告输出文件路径")
    parser.add_argument("--stamp", help="指定UTC分钟戳用于报告目录，例如 20251209-1114")
    
    args = parser.parse_args()
    
    # 显示FIO测试矩阵信息
    if args.fio_info:
        try:
            from fio_test import FIOTestRunner
            from common import Logger
            
            logger = Logger()
            fio_runner = FIOTestRunner("./", logger, args.runtime)
            matrix_info = fio_runner.get_test_matrix_info()
            
            print("\n=== FIO测试矩阵信息 ===")
            print(f"块大小: {matrix_info['block_sizes']}")
            print(f"队列深度: {matrix_info['queue_depths']}")
            print(f"并发数: {matrix_info['numjobs_values']}")
            print(f"读写比例: {matrix_info['rwmix_ratios']}%")
            print(f"总测试场景数: {matrix_info['total_scenarios']}")
            print(f"每个测试运行时间: {matrix_info['runtime_per_test']}秒")
            print(f"预计总耗时: {matrix_info['estimated_total_time_minutes']:.1f}分钟")
            
            return 0
        except Exception as e:
            print(f"获取FIO测试矩阵信息时出错: {str(e)}")
            return 1
    
    try:
        # 创建测试实例
        test_runner = StoragePerformanceTest(args.test_dir, args.runtime)
        if args.stamp:
            test_runner.run_timestamp = args.stamp
        
        print(f"\n=== 存储性能测试开始 ===")
        print(f"测试目录: {args.test_dir}")
        print(f"FIO运行时间: {args.runtime}秒")
        print(f"快速模式: {'是' if args.quick else '否'}")
        
        # 确定要运行的测试类型（默认运行所有测试）
        if not any([args.all, args.dd_only, args.fio_only]):
            args.all = True  # 默认运行所有测试
        
        include_dd = args.all or args.dd_only
        include_fio = args.all or args.fio_only
        
        if include_fio and not args.quick:
            matrix_info = test_runner.fio_runner.get_test_matrix_info()
            print(f"FIO测试场景数: {matrix_info['total_scenarios']}")
            print(f"预计FIO测试耗时: {matrix_info['estimated_total_time_minutes']:.1f}分钟")
        
        # 运行测试
        dd_results, fio_results = test_runner.run_all_tests(include_dd, include_fio, args.quick)
        
        # 生成报告
        report_file = test_runner.generate_report(dd_results, fio_results, args.output)
        
        # 打印测试摘要
        print(f"\n=== 测试摘要 ===")
        
        if dd_results:
            successful_dd = [r for r in dd_results if not r.error_message]
            print(f"DD测试: {len(successful_dd)}/{len(dd_results)} 成功")
        
        if fio_results:
            successful_fio = [r for r in fio_results if not r.error_message]
            print(f"FIO测试: {len(successful_fio)}/{len(fio_results)} 成功")
        
        print(f"\n详细报告已生成: {report_file}")
        
        # 清理测试文件
        if args.cleanup:
            test_runner.cleanup()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
