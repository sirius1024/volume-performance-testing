#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DD测试模块
包含DDTestRunner类和相关的DD命令测试功能
"""

import os
import subprocess
import time
from typing import List

from models.result import TestResult
from utils.logger import Logger
from utils.file_utils import clear_system_cache
from core_scenarios_loader import load_core_scenarios


class DDTestRunner:
    """DD测试执行器"""
    
    def __init__(self, test_dir: str, logger: Logger, core_file: str = "config/core_scenarios.json"):
        self.test_dir = test_dir
        self.logger = logger
        try:
            self.core_scenarios = load_core_scenarios(core_file).get("dd", [])
        except Exception as e:
            self.core_scenarios = []
            self.logger.warning(f"加载核心场景失败: {str(e)}")
    
    def run_all_dd_tests(self) -> List[TestResult]:
        """运行所有DD测试"""
        all_results = []
        all_results.extend(self.run_core_dd_scenarios())
        
        self.logger.info("开始运行DD测试套件")
        
        # 1. 顺序写入测试
        self.logger.info("=== 开始DD顺序写入测试 ===")
        write_results = self.run_sequential_write_tests()
        all_results.extend(write_results)
        
        # 2. 带同步选项的顺序写入测试
        self.logger.info("=== 开始DD带同步选项的顺序写入测试 ===")
        sync_write_results = self.run_sequential_write_tests_with_sync()
        all_results.extend(sync_write_results)
        
        # 3. 顺序读取测试
        self.logger.info("=== 开始DD顺序读取测试 ===")
        read_results = self.run_sequential_read_tests()
        all_results.extend(read_results)
        
        self.logger.info(f"DD测试套件完成，共执行 {len(all_results)} 个测试")
        return all_results
    
    def run_sequential_write_tests(self) -> List[TestResult]:
        """运行顺序写入测试"""
        results = []
        
        # 测试配置：块大小和文件大小的组合
        test_configs = [
            ("1G", "1G", 1),
            ("1G", "4G", 4),
            ("1M", "1G", 1024),
            ("64K", "1G", 16384),
            ("32K", "1G", 32768)
        ]
        
        for block_size, file_size, count in test_configs:
            self.logger.info(f"开始DD顺序写入测试: 块大小={block_size}, 文件大小={file_size}")
            
            test_file = f"testfile_write_{block_size.lower()}"
            command = [
                "dd",
                "if=/dev/zero",
                f"of={test_file}",
                f"bs={block_size}",
                f"count={count}",
                "oflag=direct"
            ]
            
            result = self._run_dd_command(command, "sequential_write", block_size, file_size)
            results.append(result)
        
        return results
    
    def run_sequential_write_tests_with_sync(self) -> List[TestResult]:
        """运行带同步选项的顺序写入测试"""
        results = []
        
        # 测试配置：块大小和同步选项的组合
        test_configs = [
            ("1M", "1G", 1024, "direct,dsync"),
            ("64K", "1G", 16384, "direct,dsync"),
            ("32K", "1G", 32768, "direct,dsync"),
            ("1M", "1G", 1024, "dsync"),
            ("64K", "1G", 16384, "dsync"),
            ("32K", "1G", 32768, "dsync")
        ]
        
        for block_size, file_size, count, oflag in test_configs:
            self.logger.info(f"开始DD顺序写入测试(同步): 块大小={block_size}, oflag={oflag}")
            
            test_file = f"testfile_write_{block_size.lower()}_{oflag.replace(',', '_')}"
            command = [
                "dd",
                "if=/dev/zero",
                f"of={test_file}",
                f"bs={block_size}",
                f"count={count}",
                f"oflag={oflag}"
            ]
            
            result = self._run_dd_command(command, f"sequential_write_{oflag}", block_size, file_size)
            results.append(result)
        
        return results
    
    def run_sequential_read_tests(self) -> List[TestResult]:
        """运行顺序读取测试"""
        results = []
        
        # 清除系统缓存
        self._clear_cache()
        
        # 测试配置
        test_configs = [
            ("1G", "1G", 1, "testfile_write_1g"),
            ("1G", "4G", 4, "testfile_write_1g"),
            ("1M", "1G", 1024, "testfile_write_1m"),
            ("64K", "1G", 16384, "testfile_write_64k"),
            ("32K", "1G", 32768, "testfile_write_32k")
        ]
        
        for block_size, file_size, count, input_file in test_configs:
            # 检查输入文件是否存在
            input_path = os.path.join(self.test_dir, input_file)
            if not os.path.exists(input_path):
                self.logger.warning(f"输入文件不存在，跳过测试: {input_file}")
                continue
            
            self.logger.info(f"开始DD顺序读取测试: 块大小={block_size}, 文件大小={file_size}")
            
            command = [
                "dd",
                f"if={input_file}",
                "of=/dev/null",
                f"bs={block_size}",
                f"count={count}",
                "iflag=direct"
            ]
            
            result = self._run_dd_command(command, "sequential_read", block_size, file_size)
            results.append(result)
        
        return results
    
    def run_quick_dd_tests(self) -> List[TestResult]:
        """运行快速DD测试（用于验证和调试）"""
        results = []
        results.extend(self.run_core_dd_scenarios())
        
        self.logger.info("运行快速DD测试")
        
        # 选择几个代表性的配置进行快速测试
        quick_configs = [
            # 写入测试
            ("1M", "100M", 100, "direct", "write"),
            ("64K", "100M", 1600, "direct", "write"),
            ("4K", "100M", 25600, "direct", "write"),
            # 同步写入测试
            ("1M", "100M", 100, "direct,dsync", "write"),
            ("4K", "100M", 25600, "dsync", "write")
        ]
        
        for block_size, file_size, count, oflag, test_type in quick_configs:
            self.logger.info(f"快速DD测试: {test_type} 块大小={block_size}, oflag={oflag}")
            
            test_file = f"quick_testfile_{block_size.lower()}_{oflag.replace(',', '_')}"
            
            if test_type == "write":
                command = [
                    "dd",
                    "if=/dev/zero",
                    f"of={test_file}",
                    f"bs={block_size}",
                    f"count={count}",
                    f"oflag={oflag}"
                ]
                result = self._run_dd_command(command, f"quick_sequential_write_{oflag}", block_size, file_size)
                results.append(result)
        
        # 读取测试
        self._clear_cache()
        
        read_configs = [
            ("1M", "100M", 100, "quick_testfile_1m_direct"),
            ("64K", "100M", 1600, "quick_testfile_64k_direct"),
            ("4K", "100M", 25600, "quick_testfile_4k_direct")
        ]
        
        for block_size, file_size, count, input_file in read_configs:
            input_path = os.path.join(self.test_dir, input_file)
            if not os.path.exists(input_path):
                self.logger.warning(f"快速测试输入文件不存在，跳过: {input_file}")
                continue
            
            self.logger.info(f"快速DD读取测试: 块大小={block_size}")
            
            command = [
                "dd",
                f"if={input_file}",
                "of=/dev/null",
                f"bs={block_size}",
                f"count={count}",
                "iflag=direct"
            ]
            
            result = self._run_dd_command(command, "quick_sequential_read", block_size, file_size)
            results.append(result)
        
        self.logger.info(f"快速DD测试完成，共执行 {len(results)} 个测试")
        return results

    def run_core_dd_scenarios(self) -> List[TestResult]:
        results: List[TestResult] = []
        for sc in self.core_scenarios:
            try:
                name = sc.get("name", "CORE-DD")
                t = str(sc.get("type", "write")).lower()
                bs = str(sc.get("bs", "1M")).upper()
                count = int(sc.get("count", 1024))
                oflag = sc.get("oflag", "direct")
                iflag = sc.get("iflag", "direct")
                input_file = sc.get("input_file", "")
                self.logger.info(f"[CORE] 执行DD: {name}, type={t}, bs={bs}")
                if t == "write":
                    test_file = f"core_dd_{bs.lower()}_{oflag.replace(',', '_')}"
                    cmd = [
                        "dd", "if=/dev/zero", f"of={test_file}", f"bs={bs}", f"count={count}", f"oflag={oflag}"
                    ]
                    res = self._run_dd_command(cmd, f"core_write_{oflag}", bs, f"{count}*{bs}")
                else:
                    if not input_file:
                        input_file = f"core_dd_{bs.lower()}_{oflag.replace(',', '_')}"
                    cmd = [
                        "dd", f"if={input_file}", "of=/dev/null", f"bs={bs}", f"count={count}", f"iflag={iflag}"
                    ]
                    res = self._run_dd_command(cmd, "core_read", bs, f"{count}*{bs}")
                res.test_name = f"CORE {res.test_name}"
                results.append(res)
            except Exception as e:
                self.logger.error(f"[CORE] 执行核心DD场景失败: {str(e)}")
        return results
    
    def _run_dd_command(self, command: List[str], test_type: str, block_size: str, file_size: str) -> TestResult:
        """执行DD命令"""
        result = TestResult(
            test_name=f"DD {test_type} {block_size}",
            test_type=test_type,
            command=" ".join(command),
            block_size=block_size,
            file_size=file_size
        )
        self.logger.info(f"命令: {result.command}")
        
        try:
            start_time = time.time()
            
            process = subprocess.run(
                command,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            
            if process.returncode == 0:
                # 解析DD输出
                self._parse_dd_output(process.stderr, result)
                self.logger.info(f"DD测试完成: {result.test_name}, 速度: {result.throughput_mbps:.2f} MB/s")
            else:
                result.error_message = process.stderr
                self.logger.error(f"DD测试失败: {result.test_name}, 错误: {result.error_message}")
        
        except subprocess.TimeoutExpired:
            result.error_message = "测试超时"
            self.logger.error(f"DD测试超时: {result.test_name}")
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"DD测试异常: {result.test_name}, 错误: {str(e)}")
        
        return result
    
    def _parse_dd_output(self, output: str, result: TestResult):
        """解析DD命令输出"""
        try:
            # DD输出示例: "1073741824 bytes (1.1 GB, 1.0 GiB) copied, 2.34567 s, 458 MB/s"
            lines = output.strip().split('\n')
            for line in lines:
                if 'copied' in line and 'MB/s' in line:
                    # 提取速度
                    parts = line.split(',')
                    for part in parts:
                        if 'MB/s' in part:
                            speed_str = part.strip().split()[0]
                            result.throughput_mbps = float(speed_str)
                            break
                elif 'copied' in line and 'GB/s' in line:
                    # 处理GB/s的情况
                    parts = line.split(',')
                    for part in parts:
                        if 'GB/s' in part:
                            speed_str = part.strip().split()[0]
                            result.throughput_mbps = float(speed_str) * 1024
                            break
        except Exception as e:
            self.logger.warning(f"解析DD输出时出错: {str(e)}")
    
    def _clear_cache(self):
        """清除系统缓存"""
        try:
            if clear_system_cache():
                self.logger.info("系统缓存已清除")
            else:
                self.logger.warning("清除缓存失败")
        except Exception as e:
            self.logger.warning(f"清除缓存失败: {str(e)}")
    
    def cleanup_test_files(self):
        """清理DD测试文件"""
        try:
            import glob
            test_files = glob.glob(os.path.join(self.test_dir, "testfile_*"))
            test_files.extend(glob.glob(os.path.join(self.test_dir, "quick_testfile_*")))
            
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"已删除DD测试文件: {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.warning(f"清理DD测试文件时出错: {str(e)}")


def main():
    """DD测试模块的独立运行入口"""
    import argparse
    from common import Logger, ensure_directory
    
    parser = argparse.ArgumentParser(description="DD存储性能测试工具")
    parser.add_argument("--test-dir", default="./test_data", help="测试目录路径")
    parser.add_argument("--quick", action="store_true", help="快速模式，仅运行少量代表性测试")
    parser.add_argument("--cleanup", action="store_true", help="测试完成后清理测试文件")
    
    args = parser.parse_args()
    
    # 确保测试目录存在
    if not ensure_directory(args.test_dir):
        print(f"无法创建测试目录: {args.test_dir}")
        return 1
    
    # 创建日志记录器
    logger = Logger(os.path.join(args.test_dir, "dd_test.log"))
    
    # 创建DD测试执行器
    dd_runner = DDTestRunner(args.test_dir, logger)
    
    try:
        # 运行测试
        if args.quick:
            logger.info("开始运行DD快速测试")
            results = dd_runner.run_quick_dd_tests()
        else:
            logger.info("开始运行DD完整测试套件")
            results = dd_runner.run_all_dd_tests()
        
        # 打印测试摘要
        successful_tests = [r for r in results if not r.error_message]
        failed_tests = [r for r in results if r.error_message]
        
        print(f"\n=== DD测试摘要 ===")
        print(f"总测试数: {len(results)}")
        print(f"成功: {len(successful_tests)}")
        print(f"失败: {len(failed_tests)}")
        
        if successful_tests:
            avg_speed = sum(r.throughput_mbps for r in successful_tests) / len(successful_tests)
            max_speed = max(r.throughput_mbps for r in successful_tests)
            print(f"平均速度: {avg_speed:.2f} MB/s")
            print(f"最高速度: {max_speed:.2f} MB/s")
        
        if failed_tests:
            print("\n失败的测试:")
            for test_result in failed_tests:
                print(f"- {test_result.test_name}: {test_result.error_message}")
        
        # 清理测试文件
        if args.cleanup:
            dd_runner.cleanup_test_files()
        
        return 0
    
    except KeyboardInterrupt:
        print("\nDD测试被用户中断")
        if args.cleanup:
            dd_runner.cleanup_test_files()
        return 1
    except Exception as e:
        print(f"DD测试过程中出现错误: {str(e)}")
        if args.cleanup:
            dd_runner.cleanup_test_files()
        return 1


if __name__ == "__main__":
    exit(main())
