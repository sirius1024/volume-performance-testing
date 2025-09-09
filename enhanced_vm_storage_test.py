#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版虚拟机存储性能测试工具
基于performance_test_report_template.md模板设计

功能：
1. DD命令顺序读写性能测试
2. FIO随机IO性能测试（多参数组合）
3. 系统环境信息收集
4. 测试结果解析和性能指标提取
5. 生成符合模板格式的详细测试报告
6. 多轮测试和性能波动分析
7. 性能评估和优化建议
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import threading
import platform
import psutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor


@dataclass
class SystemInfo:
    """系统信息类"""
    cpu_model: str = ""
    cpu_cores: int = 0
    memory_total_gb: float = 0.0
    os_name: str = ""
    os_version: str = ""
    kernel_version: str = ""
    storage_type: str = ""
    filesystem: str = ""
    disk_capacity_gb: float = 0.0
    available_space_gb: float = 0.0


@dataclass
class TestResult:
    """测试结果类"""
    test_name: str
    test_type: str
    command: str
    block_size: str = ""
    file_size: str = ""
    throughput_mbps: float = 0.0
    iops: float = 0.0
    latency_avg_us: float = 0.0
    latency_p95_us: float = 0.0
    latency_p99_us: float = 0.0
    duration_seconds: float = 0.0
    timestamp: str = ""
    error_message: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class Logger:
    """日志管理器"""
    
    def __init__(self, log_file: str = "enhanced_vm_storage_test.log"):
        self.logger = logging.getLogger("EnhancedVMStorageTest")
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)


class SystemInfoCollector:
    """系统信息收集器"""
    
    def __init__(self):
        self.logger = Logger()
    
    def collect_system_info(self) -> SystemInfo:
        """收集系统信息"""
        info = SystemInfo()
        
        try:
            # CPU信息
            info.cpu_model = self._get_cpu_model()
            info.cpu_cores = psutil.cpu_count(logical=False) or 0
            
            # 内存信息
            memory = psutil.virtual_memory()
            info.memory_total_gb = memory.total / (1024**3)
            
            # 操作系统信息
            info.os_name = platform.system()
            info.os_version = platform.release()
            info.kernel_version = platform.version()
            
            # 存储信息
            info.storage_type = self._get_storage_type()
            info.filesystem = self._get_filesystem()
            
            # 磁盘容量信息
            disk_usage = psutil.disk_usage('.')
            info.disk_capacity_gb = disk_usage.total / (1024**3)
            info.available_space_gb = disk_usage.free / (1024**3)
            
        except Exception as e:
            self.logger.error(f"收集系统信息时出错: {str(e)}")
        
        return info
    
    def _get_cpu_model(self) -> str:
        """获取CPU型号"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        return line.split(':')[1].strip()
        except:
            pass
        return "Unknown CPU"
    
    def _get_storage_type(self) -> str:
        """获取存储类型"""
        try:
            # 尝试检测SSD/HDD
            result = subprocess.run(['lsblk', '-d', '-o', 'name,rota'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        if parts[1] == '0':
                            return "SSD"
                        elif parts[1] == '1':
                            return "HDD"
        except:
            pass
        return "Unknown"
    
    def _get_filesystem(self) -> str:
        """获取文件系统类型"""
        try:
            result = subprocess.run(['df', '-T', '.'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        return parts[1]
        except:
            pass
        return "Unknown"


class DDTestRunner:
    """DD命令测试执行器"""
    
    def __init__(self, test_dir: str, logger: Logger):
        self.test_dir = test_dir
        self.logger = logger
    
    def run_sequential_write_tests(self) -> List[TestResult]:
        """运行顺序写入测试"""
        results = []
        
        # 测试配置：块大小和文件大小的组合
        test_configs = [
            ("1G", "1G", 1),
            ("1G", "4G", 4),
            ("1M", "1G", 1024),
            ("4K", "1G", 262144)
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
            ("4K", "1G", 262144, "testfile_write_4k")
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
    
    def _run_dd_command(self, command: List[str], test_type: str, block_size: str, file_size: str) -> TestResult:
        """执行DD命令"""
        result = TestResult(
            test_name=f"DD {test_type} {block_size}",
            test_type=test_type,
            command=" ".join(command),
            block_size=block_size,
            file_size=file_size
        )
        
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
            subprocess.run(['sync'], check=True)
            with open('/proc/sys/vm/drop_caches', 'w') as f:
                f.write('3')
            self.logger.info("系统缓存已清除")
        except Exception as e:
            self.logger.warning(f"清除缓存失败: {str(e)}")


class FIOTestRunner:
    """FIO测试执行器"""
    
    def __init__(self, test_dir: str, logger: Logger):
        self.test_dir = test_dir
        self.logger = logger
        self.runtime = 60  # 测试运行时间（秒）
    
    def run_random_io_tests(self) -> List[TestResult]:
        """运行随机IO测试"""
        results = []
        
        # 不同块大小的随机读写测试
        block_sizes = ["4k", "8k", "16k", "64k", "1m", "4m"]
        
        for block_size in block_sizes:
            # 随机读测试
            if block_size == "4k":
                read_result = self._run_fio_test(
                    f"4k_random_read",
                    "randread",
                    block_size,
                    runtime=self.runtime
                )
                results.append(read_result)
                
                # 随机写测试
                write_result = self._run_fio_test(
                    f"4k_random_write",
                    "randwrite",
                    block_size,
                    runtime=self.runtime
                )
                results.append(write_result)
            
            # 混合读写测试（50:50）
            rw_result = self._run_fio_test(
                f"{block_size}_random_rw",
                "randrw",
                block_size,
                rwmixread=50,
                runtime=self.runtime
            )
            results.append(rw_result)
        
        return results
    
    def run_queue_depth_tests(self) -> List[TestResult]:
        """运行队列深度测试"""
        results = []
        queue_depths = [1, 4, 8, 16, 32]
        
        for qd in queue_depths:
            result = self._run_fio_test(
                f"4k_qd{qd}",
                "randread",
                "4k",
                iodepth=qd,
                runtime=self.runtime
            )
            results.append(result)
        
        return results
    
    def run_mixed_ratio_tests(self) -> List[TestResult]:
        """运行混合读写比例测试"""
        results = []
        ratios = [(100, "randread"), (70, "randrw"), (50, "randrw"), (30, "randrw"), (0, "randwrite")]
        
        for read_ratio, rw_mode in ratios:
            if rw_mode == "randread":
                test_name = "100read"
            elif rw_mode == "randwrite":
                test_name = "100write"
            else:
                test_name = f"{read_ratio}read_{100-read_ratio}write"
            
            result = self._run_fio_test(
                test_name,
                rw_mode,
                "4k",
                rwmixread=read_ratio if rw_mode == "randrw" else None,
                runtime=self.runtime
            )
            results.append(result)
        
        return results
    
    def run_concurrent_tests(self) -> List[TestResult]:
        """运行并发测试"""
        results = []
        job_counts = [1, 2, 4, 8, 16, 32]
        
        for jobs in job_counts:
            result = self._run_fio_test(
                f"{jobs}jobs",
                "randrw",
                "4k",
                numjobs=jobs,
                rwmixread=50,
                runtime=self.runtime
            )
            results.append(result)
        
        return results
    
    def _run_fio_test(self, test_name: str, rw_mode: str, block_size: str, 
                     iodepth: int = 1, numjobs: int = 1, rwmixread: Optional[int] = None,
                     runtime: int = 60) -> TestResult:
        """执行FIO测试"""
        
        # 构建FIO命令
        command = [
            "fio",
            f"--name={test_name}",
            "--ioengine=libaio",
            f"--rw={rw_mode}",
            f"--bs={block_size}",
            "--direct=1",
            "--size=1G",
            f"--numjobs={numjobs}",
            f"--iodepth={iodepth}",
            f"--runtime={runtime}",
            "--group_reporting",
            "--output-format=json"
        ]
        
        if rwmixread is not None:
            command.append(f"--rwmixread={rwmixread}")
        
        result = TestResult(
            test_name=test_name,
            test_type="fio_random",
            command=" ".join(command),
            block_size=block_size
        )
        
        try:
            self.logger.info(f"开始FIO测试: {test_name}")
            start_time = time.time()
            
            process = subprocess.run(
                command,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=runtime + 60  # 额外60秒超时缓冲
            )
            
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            
            if process.returncode == 0:
                # 解析FIO JSON输出
                self._parse_fio_json_output(process.stdout, result)
                self.logger.info(f"FIO测试完成: {test_name}, IOPS: {result.iops:.0f}, 带宽: {result.throughput_mbps:.2f} MB/s")
            else:
                result.error_message = process.stderr
                self.logger.error(f"FIO测试失败: {test_name}, 错误: {result.error_message}")
        
        except subprocess.TimeoutExpired:
            result.error_message = "测试超时"
            self.logger.error(f"FIO测试超时: {test_name}")
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"FIO测试异常: {test_name}, 错误: {str(e)}")
        
        return result
    
    def _parse_fio_json_output(self, output: str, result: TestResult):
        """解析FIO JSON输出"""
        try:
            data = json.loads(output)
            
            if 'jobs' in data and len(data['jobs']) > 0:
                job = data['jobs'][0]
                
                # 提取读写性能数据
                if 'read' in job:
                    read_data = job['read']
                    if 'iops' in read_data:
                        result.iops += read_data['iops']
                    if 'bw' in read_data:
                        result.throughput_mbps += read_data['bw'] / 1024  # KB/s to MB/s
                    
                    # 延迟数据（纳秒转微秒）
                    if 'lat_ns' in read_data:
                        lat_data = read_data['lat_ns']
                        if 'mean' in lat_data:
                            result.latency_avg_us = lat_data['mean'] / 1000
                        if 'percentile' in lat_data:
                            percentiles = lat_data['percentile']
                            if '95.000000' in percentiles:
                                result.latency_p95_us = percentiles['95.000000'] / 1000
                            if '99.000000' in percentiles:
                                result.latency_p99_us = percentiles['99.000000'] / 1000
                
                if 'write' in job:
                    write_data = job['write']
                    if 'iops' in write_data:
                        result.iops += write_data['iops']
                    if 'bw' in write_data:
                        result.throughput_mbps += write_data['bw'] / 1024  # KB/s to MB/s
                    
                    # 如果没有读延迟数据，使用写延迟数据
                    if result.latency_avg_us == 0 and 'lat_ns' in write_data:
                        lat_data = write_data['lat_ns']
                        if 'mean' in lat_data:
                            result.latency_avg_us = lat_data['mean'] / 1000
                        if 'percentile' in lat_data:
                            percentiles = lat_data['percentile']
                            if '95.000000' in percentiles:
                                result.latency_p95_us = percentiles['95.000000'] / 1000
                            if '99.000000' in percentiles:
                                result.latency_p99_us = percentiles['99.000000'] / 1000
        
        except Exception as e:
            self.logger.warning(f"解析FIO JSON输出时出错: {str(e)}")
            # 尝试解析文本输出
            self._parse_fio_text_output(output, result)
    
    def _parse_fio_text_output(self, output: str, result: TestResult):
        """解析FIO文本输出（备用方法）"""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'iops=' in line:
                    # 提取IOPS
                    match = re.search(r'iops=([0-9.]+)', line)
                    if match:
                        result.iops = float(match.group(1))
                
                if 'BW=' in line or 'bw=' in line:
                    # 提取带宽
                    match = re.search(r'[Bb][Ww]=([0-9.]+)([KMG]?i?B/s)', line)
                    if match:
                        bw_value = float(match.group(1))
                        unit = match.group(2)
                        if 'MB/s' in unit or 'MiB/s' in unit:
                            result.throughput_mbps = bw_value
                        elif 'KB/s' in unit or 'KiB/s' in unit:
                            result.throughput_mbps = bw_value / 1024
                        elif 'GB/s' in unit or 'GiB/s' in unit:
                            result.throughput_mbps = bw_value * 1024
        
        except Exception as e:
            self.logger.warning(f"解析FIO文本输出时出错: {str(e)}")


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, system_info: SystemInfo, logger: Logger):
        self.system_info = system_info
        self.logger = logger
    
    def generate_report(self, all_results: List[TestResult], output_file: str = "performance_test_report.md"):
        """生成测试报告"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                self._write_header(f)
                self._write_system_info(f)
                self._write_test_methods(f)
                self._write_test_results(f, all_results)
                self._write_analysis(f, all_results)
                self._write_recommendations(f, all_results)
            
            self.logger.info(f"测试报告已生成: {output_file}")
        
        except Exception as e:
            self.logger.error(f"生成报告时出错: {str(e)}")
    
    def _write_header(self, f):
        """写入报告头部"""
        f.write("# 虚拟机存储性能测试报告\n\n")
        f.write("## 测试概述\n\n")
        f.write(f"**测试日期：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**测试工具：** Enhanced VM Storage Performance Test\n")
        f.write(f"**报告版本：** 1.0\n\n")
        f.write("---\n\n")
    
    def _write_system_info(self, f):
        """写入系统信息"""
        f.write("## 1. 测试环境配置\n\n")
        f.write("### 1.1 虚拟机规格\n\n")
        f.write("| 配置项 | 规格 | 备注 |\n")
        f.write("|--------|------|------|\n")
        f.write(f"| CPU | {self.system_info.cpu_model} | {self.system_info.cpu_cores}核 |\n")
        f.write(f"| 内存 | {self.system_info.memory_total_gb:.1f}GB | DDR4 |\n")
        f.write(f"| 操作系统 | {self.system_info.os_name} {self.system_info.os_version} | - |\n")
        f.write(f"| 内核版本 | {self.system_info.kernel_version} | - |\n")
        f.write(f"| 存储类型 | {self.system_info.storage_type} | - |\n")
        f.write(f"| 文件系统 | {self.system_info.filesystem} | - |\n")
        f.write(f"| 磁盘容量 | {self.system_info.disk_capacity_gb:.1f}GB | 可用空间: {self.system_info.available_space_gb:.1f}GB |\n\n")
        
        f.write("### 1.2 测试工具版本\n\n")
        f.write("| 工具 | 版本 | 用途 |\n")
        f.write("|------|------|------|\n")
        f.write("| dd | GNU coreutils | 顺序读写性能测试 |\n")
        f.write("| fio | 3.x | 随机IO性能测试 |\n")
        f.write("| Python | 3.x | 测试脚本执行环境 |\n\n")
        f.write("---\n\n")
    
    def _write_test_methods(self, f):
        """写入测试方法"""
        f.write("## 2. 测试方法\n\n")
        f.write("### 2.1 DD命令顺序读写测试\n\n")
        f.write("#### 2.1.1 顺序写入测试\n\n")
        f.write("**测试命令：**\n")
        f.write("```bash\n")
        f.write("# 1GB文件写入测试\n")
        f.write("dd if=/dev/zero of=testfile_1g bs=1G count=1 oflag=direct\n\n")
        f.write("# 4GB文件写入测试\n")
        f.write("dd if=/dev/zero of=testfile_4g bs=1G count=4 oflag=direct\n\n")
        f.write("# 不同块大小写入测试\n")
        f.write("dd if=/dev/zero of=testfile_1m bs=1M count=1024 oflag=direct\n")
        f.write("dd if=/dev/zero of=testfile_4k bs=4K count=262144 oflag=direct\n")
        f.write("```\n\n")
        
        f.write("#### 2.1.2 顺序读取测试\n\n")
        f.write("**测试命令：**\n")
        f.write("```bash\n")
        f.write("# 清除系统缓存\n")
        f.write("echo 3 > /proc/sys/vm/drop_caches\n\n")
        f.write("# 读取测试\n")
        f.write("dd if=testfile_1g of=/dev/null bs=1G count=1 iflag=direct\n")
        f.write("dd if=testfile_4g of=/dev/null bs=1G count=4 iflag=direct\n")
        f.write("```\n\n")
        
        f.write("### 2.2 FIO命令随机IO测试\n\n")
        f.write("#### 2.2.1 随机读写性能测试\n\n")
        f.write("**4K随机读测试：**\n")
        f.write("```bash\n")
        f.write("fio --name=4k_random_read --ioengine=libaio --rw=randread --bs=4k --direct=1 --size=1G --numjobs=1 --runtime=60 --group_reporting\n")
        f.write("```\n\n")
        f.write("---\n\n")
    
    def _write_test_results(self, f, all_results: List[TestResult]):
        """写入测试结果"""
        f.write("## 3. 测试结果\n\n")
        
        # DD测试结果
        dd_results = [r for r in all_results if r.test_type in ['sequential_write', 'sequential_read']]
        if dd_results:
            self._write_dd_results(f, dd_results)
        
        # FIO测试结果
        fio_results = [r for r in all_results if r.test_type == 'fio_random']
        if fio_results:
            self._write_fio_results(f, fio_results)
    
    def _write_dd_results(self, f, dd_results: List[TestResult]):
        """写入DD测试结果"""
        f.write("### 3.1 DD命令顺序读写测试结果\n\n")
        
        # 写入测试结果
        write_results = [r for r in dd_results if r.test_type == 'sequential_write']
        if write_results:
            f.write("#### 3.1.1 顺序写入性能\n\n")
            f.write("| 块大小 | 文件大小 | 写入速度 | 耗时 | 命令 |\n")
            f.write("|--------|----------|----------|------|------|\n")
            for result in write_results:
                f.write(f"| {result.block_size} | {result.file_size} | {result.throughput_mbps:.2f} MB/s | {result.duration_seconds:.2f} s | `{result.command}` |\n")
            f.write("\n")
        
        # 读取测试结果
        read_results = [r for r in dd_results if r.test_type == 'sequential_read']
        if read_results:
            f.write("#### 3.1.2 顺序读取性能\n\n")
            f.write("| 块大小 | 文件大小 | 读取速度 | 耗时 | 命令 |\n")
            f.write("|--------|----------|----------|------|------|\n")
            for result in read_results:
                f.write(f"| {result.block_size} | {result.file_size} | {result.throughput_mbps:.2f} MB/s | {result.duration_seconds:.2f} s | `{result.command}` |\n")
            f.write("\n")
    
    def _write_fio_results(self, f, fio_results: List[TestResult]):
        """写入FIO测试结果"""
        f.write("### 3.2 FIO随机IO测试结果\n\n")
        
        # 不同块大小测试结果
        block_size_results = [r for r in fio_results if 'random_rw' in r.test_name or 'random_read' in r.test_name or 'random_write' in r.test_name]
        if block_size_results:
            f.write("#### 3.2.1 不同块大小随机读写性能\n\n")
            f.write("| 块大小 | 读写模式 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |\n")
            f.write("|--------|----------|------|------------|--------------|-------------|------|\n")
            for result in block_size_results:
                mode = "随机读" if "read" in result.test_name else "随机写" if "write" in result.test_name else "随机读写"
                f.write(f"| {result.block_size} | {mode} | {result.iops:.0f} | {result.throughput_mbps:.2f} | {result.latency_avg_us:.0f} | {result.latency_p99_us:.0f} | `{result.command}` |\n")
            f.write("\n")
        
        # 队列深度测试结果
        qd_results = [r for r in fio_results if 'qd' in r.test_name]
        if qd_results:
            f.write("#### 3.2.2 队列深度对性能的影响\n\n")
            f.write("| 队列深度 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |\n")
            f.write("|----------|------|------------|--------------|-------------|------|\n")
            for result in qd_results:
                qd = result.test_name.replace('4k_qd', '')
                f.write(f"| {qd} | {result.iops:.0f} | {result.throughput_mbps:.2f} | {result.latency_avg_us:.0f} | {result.latency_p99_us:.0f} | `{result.command}` |\n")
            f.write("\n")
        
        # 混合读写比例测试结果
        ratio_results = [r for r in fio_results if 'read' in r.test_name and 'write' in r.test_name or r.test_name in ['100read', '100write']]
        if ratio_results:
            f.write("#### 3.2.3 混合读写比例测试结果\n\n")
            f.write("| 读写比例 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |\n")
            f.write("|----------|------|------------|--------------|-------------|------|\n")
            for result in ratio_results:
                ratio = result.test_name.replace('read', '%读').replace('write', '%写')
                f.write(f"| {ratio} | {result.iops:.0f} | {result.throughput_mbps:.2f} | {result.latency_avg_us:.0f} | {result.latency_p99_us:.0f} | `{result.command}` |\n")
            f.write("\n")
        
        # 并发测试结果
        concurrent_results = [r for r in fio_results if 'jobs' in r.test_name]
        if concurrent_results:
            f.write("#### 3.2.4 并发测试结果\n\n")
            f.write("| 并发数 | IOPS | 带宽(MB/s) | 平均延迟(μs) | 99%延迟(μs) | 命令 |\n")
            f.write("|--------|------|------------|--------------|-------------|------|\n")
            for result in concurrent_results:
                jobs = result.test_name.replace('jobs', '')
                f.write(f"| {jobs} | {result.iops:.0f} | {result.throughput_mbps:.2f} | {result.latency_avg_us:.0f} | {result.latency_p99_us:.0f} | `{result.command}` |\n")
            f.write("\n")
    
    def _write_analysis(self, f, all_results: List[TestResult]):
        """写入性能分析"""
        f.write("## 4. 性能分析\n\n")
        
        # 计算关键性能指标
        valid_results = [r for r in all_results if not r.error_message]
        
        if valid_results:
            # 顺序读写性能
            seq_read_results = [r for r in valid_results if r.test_type == 'sequential_read']
            seq_write_results = [r for r in valid_results if r.test_type == 'sequential_write']
            
            # 随机IO性能
            random_read_results = [r for r in valid_results if 'random_read' in r.test_name]
            random_write_results = [r for r in valid_results if 'random_write' in r.test_name]
            
            f.write("### 4.1 关键性能指标汇总\n\n")
            f.write("| 测试类型 | 最佳性能 | 平均性能 | 最差性能 |\n")
            f.write("|----------|----------|----------|----------|\n")
            
            if seq_read_results:
                read_speeds = [r.throughput_mbps for r in seq_read_results]
                f.write(f"| 顺序读取速度 | {max(read_speeds):.2f} MB/s | {sum(read_speeds)/len(read_speeds):.2f} MB/s | {min(read_speeds):.2f} MB/s |\n")
            
            if seq_write_results:
                write_speeds = [r.throughput_mbps for r in seq_write_results]
                f.write(f"| 顺序写入速度 | {max(write_speeds):.2f} MB/s | {sum(write_speeds)/len(write_speeds):.2f} MB/s | {min(write_speeds):.2f} MB/s |\n")
            
            if random_read_results:
                read_iops = [r.iops for r in random_read_results]
                f.write(f"| 4K随机读IOPS | {max(read_iops):.0f} | {sum(read_iops)/len(read_iops):.0f} | {min(read_iops):.0f} |\n")
            
            if random_write_results:
                write_iops = [r.iops for r in random_write_results]
                f.write(f"| 4K随机写IOPS | {max(write_iops):.0f} | {sum(write_iops)/len(write_iops):.0f} | {min(write_iops):.0f} |\n")
            
            f.write("\n")
    
    def _write_recommendations(self, f, all_results: List[TestResult]):
        """写入优化建议"""
        f.write("## 5. 结论与建议\n\n")
        
        f.write("### 5.1 存储性能评估\n\n")
        
        # 基于测试结果给出评估
        valid_results = [r for r in all_results if not r.error_message]
        
        if valid_results:
            # 计算平均性能
            seq_results = [r for r in valid_results if r.test_type in ['sequential_read', 'sequential_write']]
            random_results = [r for r in valid_results if r.test_type == 'fio_random']
            
            if seq_results:
                avg_seq_speed = sum(r.throughput_mbps for r in seq_results) / len(seq_results)
                f.write(f"**顺序读写性能：** 平均速度 {avg_seq_speed:.2f} MB/s\n")
                
                if avg_seq_speed > 500:
                    f.write("- 性能等级：优秀\n")
                elif avg_seq_speed > 200:
                    f.write("- 性能等级：良好\n")
                elif avg_seq_speed > 100:
                    f.write("- 性能等级：一般\n")
                else:
                    f.write("- 性能等级：较差\n")
            
            if random_results:
                avg_iops = sum(r.iops for r in random_results) / len(random_results)
                f.write(f"\n**随机IO性能：** 平均IOPS {avg_iops:.0f}\n")
                
                if avg_iops > 10000:
                    f.write("- 性能等级：优秀\n")
                elif avg_iops > 5000:
                    f.write("- 性能等级：良好\n")
                elif avg_iops > 1000:
                    f.write("- 性能等级：一般\n")
                else:
                    f.write("- 性能等级：较差\n")
        
        f.write("\n### 5.2 优化建议\n\n")
        f.write("**硬件优化：**\n")
        f.write("- 考虑升级到更高性能的SSD存储\n")
        f.write("- 增加内存容量以提高缓存效果\n")
        f.write("- 优化RAID配置以平衡性能和可靠性\n\n")
        
        f.write("**软件优化：**\n")
        f.write("- 调整IO调度器参数\n")
        f.write("- 优化文件系统挂载参数\n")
        f.write("- 调整应用程序的IO模式\n\n")
        
        f.write("**监控建议：**\n")
        f.write("- 持续监控IOPS和延迟指标\n")
        f.write("- 设置性能告警阈值\n")
        f.write("- 定期进行性能基准测试\n\n")


class EnhancedVMStorageTest:
    """增强版虚拟机存储性能测试主类"""
    
    def __init__(self, test_dir: str = "./test_data"):
        self.test_dir = test_dir
        self.logger = Logger()
        
        # 创建测试目录
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 初始化组件
        self.system_collector = SystemInfoCollector()
        self.dd_runner = DDTestRunner(self.test_dir, self.logger)
        self.fio_runner = FIOTestRunner(self.test_dir, self.logger)
        
        self.logger.info(f"增强版虚拟机存储性能测试初始化完成，测试目录: {self.test_dir}")
    
    def run_all_tests(self) -> List[TestResult]:
        """运行所有测试"""
        all_results = []
        
        self.logger.info("开始运行所有存储性能测试")
        
        try:
            # 1. DD顺序写入测试
            self.logger.info("=== 开始DD顺序写入测试 ===")
            write_results = self.dd_runner.run_sequential_write_tests()
            all_results.extend(write_results)
            
            # 2. DD顺序读取测试
            self.logger.info("=== 开始DD顺序读取测试 ===")
            read_results = self.dd_runner.run_sequential_read_tests()
            all_results.extend(read_results)
            
            # 3. FIO随机IO测试
            self.logger.info("=== 开始FIO随机IO测试 ===")
            random_results = self.fio_runner.run_random_io_tests()
            all_results.extend(random_results)
            
            # 4. FIO队列深度测试
            self.logger.info("=== 开始FIO队列深度测试 ===")
            qd_results = self.fio_runner.run_queue_depth_tests()
            all_results.extend(qd_results)
            
            # 5. FIO混合读写比例测试
            self.logger.info("=== 开始FIO混合读写比例测试 ===")
            ratio_results = self.fio_runner.run_mixed_ratio_tests()
            all_results.extend(ratio_results)
            
            # 6. FIO并发测试
            self.logger.info("=== 开始FIO并发测试 ===")
            concurrent_results = self.fio_runner.run_concurrent_tests()
            all_results.extend(concurrent_results)
            
            self.logger.info(f"所有测试完成，共执行 {len(all_results)} 个测试")
            
        except Exception as e:
            self.logger.error(f"测试过程中出现异常: {str(e)}")
        
        return all_results
    
    def generate_report(self, results: List[TestResult], output_file: str = "performance_test_report.md"):
        """生成测试报告"""
        # 收集系统信息
        system_info = self.system_collector.collect_system_info()
        
        # 生成报告
        report_generator = ReportGenerator(system_info, self.logger)
        report_generator.generate_report(results, output_file)
    
    def cleanup(self):
        """清理测试文件"""
        try:
            import glob
            test_files = glob.glob(os.path.join(self.test_dir, "testfile_*"))
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"已删除测试文件: {file_path}")
        except Exception as e:
            self.logger.warning(f"清理测试文件时出错: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="增强版虚拟机存储性能测试工具")
    parser.add_argument("--test-dir", default="./test_data", help="测试目录路径")
    parser.add_argument("--output", default="performance_test_report.md", help="报告输出文件")
    parser.add_argument("--cleanup", action="store_true", help="测试完成后清理测试文件")
    
    args = parser.parse_args()
    
    # 创建测试实例
    test = EnhancedVMStorageTest(args.test_dir)
    
    try:
        # 运行所有测试
        results = test.run_all_tests()
        
        # 生成报告
        test.generate_report(results, args.output)
        
        # 打印测试摘要
        successful_tests = [r for r in results if not r.error_message]
        failed_tests = [r for r in results if r.error_message]
        
        print(f"\n=== 测试摘要 ===")
        print(f"总测试数: {len(results)}")
        print(f"成功: {len(successful_tests)}")
        print(f"失败: {len(failed_tests)}")
        
        if failed_tests:
            print("\n失败的测试:")
            for test_result in failed_tests:
                print(f"- {test_result.test_name}: {test_result.error_message}")
        
        print(f"\n详细报告已生成: {args.output}")
        
        # 清理测试文件
        if args.cleanup:
            test.cleanup()
    
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        if args.cleanup:
            test.cleanup()
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        if args.cleanup:
            test.cleanup()


if __name__ == "__main__":
    main()