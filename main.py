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

from common import TestResult, Logger, SystemInfoCollector, ensure_directory
from dd_test import DDTestRunner
from fio_test import FIOTestRunner


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def generate_report(self, dd_results: List[TestResult], fio_results: List[TestResult], 
                       output_file: str, system_info: Optional[dict] = None, core_results: Optional[List[TestResult]] = None):
        """生成综合测试报告"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                self._write_header(f)
                
                if system_info:
                    self._write_system_info(f, system_info)
                
                if system_info and core_results is not None:
                    self._write_core_section(f, core_results)
                
                if dd_results:
                    self._write_dd_results(f, dd_results)
                
                if fio_results:
                    self._write_fio_results(f, fio_results)
                
                self._write_summary(f, dd_results, fio_results)
                
            self.logger.info(f"测试报告已生成: {output_file}")
        
        except Exception as e:
            self.logger.error(f"生成报告时出错: {str(e)}")
    
    def _write_core_section(self, f, core_results: List[TestResult]):
        f.write("## 核心业务场景\n\n")
        if not core_results:
            f.write("*无核心场景结果*\n\n")
            return
        successful = [r for r in core_results if not r.error_message]
        failed = [r for r in core_results if r.error_message]
        f.write(f"### 场景概览\n")
        f.write(f"- 总数: {len(core_results)}\n")
        f.write(f"- 成功: {len(successful)}\n")
        f.write(f"- 失败: {len(failed)}\n\n")
        # FIO类结果表
        fio_like = [r for r in core_results if r.test_type in ("randread", "randwrite", "randrw", "read", "write")]
        if fio_like:
            f.write("### FIO核心场景\n\n")
            f.write("| 名称 | 块大小 | 队列深度 | 并发 | 读IOPS | 写IOPS | 读MB/s | 写MB/s | 读延迟(μs) | 写延迟(μs) | 状态 |\n")
            f.write("|------|--------|----------|------|--------|--------|--------|--------|-------------|-------------|------|\n")
            for r in fio_like[:30]:
                status = "成功" if not r.error_message else "失败"
                f.write(f"| {r.test_name} | {r.block_size} | {getattr(r,'queue_depth',0)} | {getattr(r,'numjobs',0)} | "
                        f"{getattr(r,'read_iops',0):.0f} | {getattr(r,'write_iops',0):.0f} | "
                        f"{getattr(r,'read_mbps',0):.2f} | {getattr(r,'write_mbps',0):.2f} | "
                        f"{getattr(r,'read_latency_us',0):.1f} | {getattr(r,'write_latency_us',0):.1f} | {status} |\n")
            f.write("\n")
        # 失败列表
        if failed:
            f.write("### 失败详情\n\n")
            for r in failed[:10]:
                f.write(f"- {r.test_name}: {r.error_message}\n")
            f.write("\n")
    
    def _write_header(self, f):
        """写入报告头部"""
        f.write("# 存储性能测试报告\n\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    def _write_system_info(self, f, system_info):
        """写入系统信息"""
        f.write("## 系统信息\n\n")
        f.write(f"- 操作系统: {system_info.os_name} {system_info.os_version}\n")
        f.write(f"- 内核版本: {system_info.kernel_version}\n")
        f.write(f"- CPU: {system_info.cpu_model} ({system_info.cpu_cores}核)\n")
        f.write(f"- 内存: {system_info.memory_total_gb:.1f} GB\n")
        f.write(f"- 存储设备: {system_info.storage_type}\n")
        f.write(f"- 文件系统: {system_info.filesystem}\n")
        f.write(f"- 磁盘容量: {system_info.disk_capacity_gb:.1f} GB (可用: {system_info.available_space_gb:.1f} GB)\n\n")
    
    def _write_dd_results(self, f, dd_results: List[TestResult]):
        """写入DD测试结果"""
        f.write("## DD测试结果\n\n")
        
        successful_tests = [r for r in dd_results if not r.error_message]
        failed_tests = [r for r in dd_results if r.error_message]
        
        f.write(f"### 测试概览\n")
        f.write(f"- 总测试数: {len(dd_results)}\n")
        f.write(f"- 成功: {len(successful_tests)}\n")
        f.write(f"- 失败: {len(failed_tests)}\n\n")
        
        if successful_tests:
            f.write("### 成功测试详情\n\n")
            f.write("| 测试名称 | 块大小 | 文件大小 | 吞吐量(MB/s) | 耗时(秒) |\n")
            f.write("|----------|--------|----------|-------------|----------|\n")
            
            for result in successful_tests:
                f.write(f"| {result.test_name} | {result.block_size} | {result.file_size} | "
                       f"{result.throughput_mbps:.2f} | {result.duration_seconds:.2f} |\n")
            f.write("\n")
        
        if failed_tests:
            f.write("### 失败测试\n\n")
            for result in failed_tests:
                f.write(f"- {result.test_name}: {result.error_message}\n")
            f.write("\n")
    
    def _write_fio_results(self, f, fio_results: List[TestResult]):
        """写入FIO测试结果"""
        f.write("## FIO测试结果\n\n")
        
        successful_tests = [r for r in fio_results if not r.error_message]
        failed_tests = [r for r in fio_results if r.error_message]
        
        f.write(f"### 测试概览\n")
        f.write(f"- 总测试数: {len(fio_results)}\n")
        f.write(f"- 成功: {len(successful_tests)}\n")
        f.write(f"- 失败: {len(failed_tests)}\n\n")
        
        if successful_tests:
            # 排除核心场景，仅展示普通FIO结果
            normal_success = [r for r in successful_tests if not r.test_name.startswith("CORE ")]
            # 按测试类型分组显示
            read_tests = [r for r in normal_success if r.read_iops > 0 and r.write_iops == 0]
            write_tests = [r for r in normal_success if r.write_iops > 0 and r.read_iops == 0]
            mixed_tests = [r for r in normal_success if r.read_iops > 0 and r.write_iops > 0]
            
            if read_tests:
                f.write("### 随机读测试\n\n")
                f.write("| 测试名称 | 块大小 | 队列深度 | 并发数 | IOPS | 吞吐量(MB/s) | 延迟(μs) |\n")
                f.write("|----------|--------|----------|--------|------|-------------|----------|\n")
                
                for result in read_tests:  # 全量显示
                    f.write(f"| {result.test_name} | {result.block_size} | {result.queue_depth} | "
                           f"{result.numjobs} | {result.read_iops:.0f} | {result.read_mbps:.2f} | "
                           f"{result.read_latency_us:.1f} |\n")
                
                f.write("\n")
            
            if write_tests:
                f.write("### 随机写测试\n\n")
                f.write("| 测试名称 | 块大小 | 队列深度 | 并发数 | IOPS | 吞吐量(MB/s) | 延迟(μs) |\n")
                f.write("|----------|--------|----------|--------|------|-------------|----------|\n")
                
                for result in write_tests:  # 全量显示
                    f.write(f"| {result.test_name} | {result.block_size} | {result.queue_depth} | "
                           f"{result.numjobs} | {result.write_iops:.0f} | {result.write_mbps:.2f} | "
                           f"{result.write_latency_us:.1f} |\n")
                
                f.write("\n")
            
            if mixed_tests:
                f.write("### 随机读写混合测试\n\n")
                f.write("| 测试名称 | 块大小 | 队列深度 | 并发数 | 读IOPS | 写IOPS | 总吞吐量(MB/s) |\n")
                f.write("|----------|--------|----------|--------|--------|--------|---------------|\n")
                
                for result in mixed_tests:  # 全量显示
                    f.write(f"| {result.test_name} | {result.block_size} | {result.queue_depth} | "
                           f"{result.numjobs} | {result.read_iops:.0f} | {result.write_iops:.0f} | "
                           f"{result.throughput_mbps:.2f} |\n")
                
                f.write("\n")
        
        if failed_tests:
            f.write("### 失败测试\n\n")
            for result in failed_tests[:10]:  # 限制显示数量
                f.write(f"- {result.test_name}: {result.error_message}\n")
            if len(failed_tests) > 10:
                f.write(f"\n... 还有 {len(failed_tests) - 10} 个失败测试\n")
            f.write("\n")
    
    def _write_summary(self, f, dd_results: List[TestResult], fio_results: List[TestResult]):
        """写入测试摘要"""
        f.write("## 测试摘要\n\n")
        
        # DD测试摘要
        if dd_results:
            successful_dd = [r for r in dd_results if not r.error_message]
            if successful_dd:
                avg_dd_speed = sum(r.throughput_mbps for r in successful_dd) / len(successful_dd)
                max_dd_speed = max(r.throughput_mbps for r in successful_dd)
                f.write(f"### DD测试性能\n")
                f.write(f"- 平均吞吐量: {avg_dd_speed:.2f} MB/s\n")
                f.write(f"- 最高吞吐量: {max_dd_speed:.2f} MB/s\n\n")
        
        # FIO测试摘要
        if fio_results:
            successful_fio = [r for r in fio_results if not r.error_message]
            if successful_fio:
                read_tests = [r for r in successful_fio if r.read_iops > 0]
                write_tests = [r for r in successful_fio if r.write_iops > 0]
                
                f.write(f"### FIO测试性能\n")
                
                if read_tests:
                    avg_read_iops = sum(r.read_iops for r in read_tests) / len(read_tests)
                    max_read_iops = max(r.read_iops for r in read_tests)
                    f.write(f"- 平均读取IOPS: {avg_read_iops:.0f}\n")
                    f.write(f"- 最高读取IOPS: {max_read_iops:.0f}\n")
                
                if write_tests:
                    avg_write_iops = sum(r.write_iops for r in write_tests) / len(write_tests)
                    max_write_iops = max(r.write_iops for r in write_tests)
                    f.write(f"- 平均写入IOPS: {avg_write_iops:.0f}\n")
                    f.write(f"- 最高写入IOPS: {max_write_iops:.0f}\n")
                
                f.write("\n")
        
        # 总体结论
        f.write("### 结论\n\n")
        total_tests = len(dd_results) + len(fio_results)
        total_successful = len([r for r in dd_results + fio_results if not r.error_message])
        success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        
        f.write(f"本次测试共执行 {total_tests} 个测试场景，成功率为 {success_rate:.1f}%。\n\n")
        
        if success_rate >= 95:
            f.write("存储设备性能表现良好，各项指标正常。\n")
        elif success_rate >= 80:
            f.write("存储设备性能基本正常，但存在少量异常情况，建议进一步检查。\n")
        else:
            f.write("存储设备性能存在较多问题，建议详细检查硬件和配置。\n")


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
        self.dd_runner = DDTestRunner(test_dir, self.logger, core_file="config/core_scenarios.yaml")
        self.fio_runner = FIOTestRunner(test_dir, self.logger, runtime, core_file="config/core_scenarios.yaml")
        
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
            ts = self.run_timestamp or time.strftime('%Y%m%d-%H%M')
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
        self.run_timestamp = time.strftime('%Y%m%d-%H%M')
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
            ts = self.run_timestamp or time.strftime('%Y%m%d-%H%M')
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
