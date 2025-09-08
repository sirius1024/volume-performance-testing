#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟机存储性能测试工具

功能：
1. 顺序读写性能测试
2. 随机读写性能测试（多参数组合）
3. 并发性能测试
4. 突发性能与多文件并发测试
5. I/O对齐敏感度测试
6. 系统资源监控
7. 测试报告生成
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import threading
import multiprocessing
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


@dataclass
class TestConfig:
    """测试配置类"""
    # 基础配置
    test_dir: str = "./test_data"
    test_file_size: str = "1G"
    runtime: int = 60  # 测试运行时间（秒）
    
    # 顺序读写测试配置
    sequential_block_sizes: List[str] = None
    
    # 随机读写测试配置
    random_block_sizes: List[str] = None
    read_write_ratios: List[str] = None
    queue_depths: List[int] = None
    write_modes: List[str] = None
    
    # 并发测试配置
    max_threads: int = 16
    max_processes: int = 8
    
    # 突发测试配置
    burst_duration: int = 10
    max_files: int = 64
    
    # I/O对齐测试配置
    alignment_offsets: List[str] = None
    
    def __post_init__(self):
        if self.sequential_block_sizes is None:
            self.sequential_block_sizes = ["1M", "4M", "8M", "16M"]
        
        if self.random_block_sizes is None:
            self.random_block_sizes = ["4K", "8K", "16K", "32K", "64K", "128K", "1M", "2M", "4M"]
        
        if self.read_write_ratios is None:
            self.read_write_ratios = ["100:0", "70:30", "50:50", "30:70", "0:100"]
        
        if self.queue_depths is None:
            self.queue_depths = [1, 4, 8, 16, 32, 64, 128]
        
        if self.write_modes is None:
            self.write_modes = ["sync", "dsync", "direct"]
        
        if self.alignment_offsets is None:
            self.alignment_offsets = ["512", "4K"]


@dataclass
class PerformanceBottleneck:
    """性能瓶颈分析结果"""
    factor: str  # 影响因素名称
    impact_score: float  # 影响分数 (0-100)
    description: str  # 描述
    recommendation: str  # 优化建议


@dataclass
class PerformanceAnalysis:
    """性能分析结果"""
    top1_bottleneck: PerformanceBottleneck
    top3_bottlenecks: List[PerformanceBottleneck]
    overall_performance_score: float  # 整体性能分数 (0-100)
    analysis_summary: str  # 分析总结
    optimization_suggestions: List[str]  # 优化建议列表


@dataclass
class TestResult:
    """测试结果类"""
    test_name: str
    test_type: str
    parameters: Dict[str, Any]
    throughput_mbps: float = 0.0
    iops: float = 0.0
    latency_avg_ms: float = 0.0
    latency_max_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    network_bandwidth_mbps: float = 0.0
    timestamp: str = ""
    duration: float = 0.0
    error_message: str = ""
    performance_analysis: PerformanceAnalysis = None  # 性能瓶颈分析结果
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class Logger:
    """日志管理器"""
    
    def __init__(self, log_file: str = "vm_storage_test.log"):
        self.logger = logging.getLogger("VMStorageTest")
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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


class SystemMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.cpu_usage = []
        self.memory_usage = []
        self.network_usage = []
        self.disk_io_stats = []
        self.monitor_thread = None
        self.start_time = None
        self.initial_network_stats = None
        self.initial_disk_stats = None
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.start_time = time.time()
        self.cpu_usage.clear()
        self.memory_usage.clear()
        self.network_usage.clear()
        self.disk_io_stats.clear()
        
        # 获取初始网络和磁盘统计信息
        self.initial_network_stats = self._get_network_stats()
        self.initial_disk_stats = self._get_disk_stats()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 监控CPU使用率
                cpu_percent = self._get_cpu_usage()
                if cpu_percent is not None:
                    self.cpu_usage.append(cpu_percent)
                
                # 监控内存使用率
                memory_percent = self._get_memory_usage()
                if memory_percent is not None:
                    self.memory_usage.append(memory_percent)
                
                # 监控网络使用率
                network_mbps = self._get_network_usage()
                if network_mbps is not None:
                    self.network_usage.append(network_mbps)
                
                # 监控磁盘I/O
                disk_io = self._get_disk_io_usage()
                if disk_io is not None:
                    self.disk_io_stats.append(disk_io)
                
                time.sleep(1)
            except Exception as e:
                # 如果监控出错，继续运行但记录错误
                time.sleep(1)
                continue
    
    def _get_cpu_usage(self):
        """获取CPU使用率"""
        try:
            # 尝试使用 /proc/stat 获取CPU使用率
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                cpu_times = [int(x) for x in line.split()[1:]]
                idle_time = cpu_times[3]
                total_time = sum(cpu_times)
                
                if hasattr(self, '_prev_idle') and hasattr(self, '_prev_total'):
                    idle_delta = idle_time - self._prev_idle
                    total_delta = total_time - self._prev_total
                    if total_delta > 0:
                        cpu_percent = 100.0 * (1.0 - idle_delta / total_delta)
                    else:
                        cpu_percent = 0.0
                else:
                    cpu_percent = 0.0
                
                self._prev_idle = idle_time
                self._prev_total = total_time
                return cpu_percent
        except:
            # 如果读取 /proc/stat 失败，尝试使用 top 命令
            try:
                result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if 'Cpu(s):' in line or '%Cpu(s):' in line:
                        # 解析类似 "Cpu(s): 12.5%us, 2.3%sy, 0.0%ni, 84.8%id" 的行
                        parts = line.split(',')
                        for part in parts:
                            if 'id' in part:  # idle
                                idle_str = part.strip().split('%')[0]
                                idle_percent = float(idle_str.split()[-1])
                                return 100.0 - idle_percent
                return None
            except:
                return None
    
    def _get_memory_usage(self):
        """获取内存使用率"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # 解析内存信息
            lines = meminfo.split('\n')
            mem_total = 0
            mem_available = 0
            
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024  # 转换为字节
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) * 1024  # 转换为字节
            
            if mem_total > 0:
                mem_used = mem_total - mem_available
                return (mem_used / mem_total) * 100.0
            return None
        except:
            # 如果读取 /proc/meminfo 失败，尝试使用 free 命令
            try:
                result = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.startswith('Mem:'):
                        parts = line.split()
                        total = float(parts[1])
                        used = float(parts[2])
                        return (used / total) * 100.0
                return None
            except:
                return None
    
    def _get_network_stats(self):
        """获取网络统计信息"""
        try:
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()
            
            total_rx_bytes = 0
            total_tx_bytes = 0
            
            for line in lines[2:]:  # 跳过头两行
                parts = line.split()
                if len(parts) >= 10:
                    interface = parts[0].rstrip(':')
                    # 跳过回环接口
                    if interface != 'lo':
                        rx_bytes = int(parts[1])
                        tx_bytes = int(parts[9])
                        total_rx_bytes += rx_bytes
                        total_tx_bytes += tx_bytes
            
            return {
                'rx_bytes': total_rx_bytes,
                'tx_bytes': total_tx_bytes,
                'total_bytes': total_rx_bytes + total_tx_bytes
            }
        except:
            return None
    
    def _get_network_usage(self):
        """获取网络使用率（MB/s）"""
        try:
            current_stats = self._get_network_stats()
            if current_stats is None or self.initial_network_stats is None:
                return 0.0
            
            if hasattr(self, '_prev_network_stats') and self._prev_network_stats:
                # 计算与上一次的差值
                time_delta = 1.0  # 1秒间隔
                bytes_delta = current_stats['total_bytes'] - self._prev_network_stats['total_bytes']
                mbps = (bytes_delta / (1024 * 1024)) / time_delta
                self._prev_network_stats = current_stats
                return max(0, mbps)
            else:
                self._prev_network_stats = current_stats
                return 0.0
        except:
            return 0.0
    
    def _get_disk_stats(self):
        """获取磁盘统计信息"""
        try:
            with open('/proc/diskstats', 'r') as f:
                lines = f.readlines()
            
            total_read_ops = 0
            total_write_ops = 0
            total_read_sectors = 0
            total_write_sectors = 0
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 14:
                    device = parts[2]
                    # 只统计主要磁盘设备（排除分区和虚拟设备）
                    if device.startswith(('sd', 'hd', 'vd', 'nvme')):
                        read_ops = int(parts[3])
                        write_ops = int(parts[7])
                        read_sectors = int(parts[5])
                        write_sectors = int(parts[9])
                        
                        total_read_ops += read_ops
                        total_write_ops += write_ops
                        total_read_sectors += read_sectors
                        total_write_sectors += write_sectors
            
            return {
                'read_ops': total_read_ops,
                'write_ops': total_write_ops,
                'read_sectors': total_read_sectors,
                'write_sectors': total_write_sectors
            }
        except:
            return None
    
    def _get_disk_io_usage(self):
        """获取磁盘I/O使用率"""
        try:
            current_stats = self._get_disk_stats()
            if current_stats is None:
                return None
            
            if hasattr(self, '_prev_disk_stats') and self._prev_disk_stats:
                # 计算与上一次的差值
                read_ops_delta = current_stats['read_ops'] - self._prev_disk_stats['read_ops']
                write_ops_delta = current_stats['write_ops'] - self._prev_disk_stats['write_ops']
                read_sectors_delta = current_stats['read_sectors'] - self._prev_disk_stats['read_sectors']
                write_sectors_delta = current_stats['write_sectors'] - self._prev_disk_stats['write_sectors']
                
                # 扇区大小通常是512字节
                sector_size = 512
                read_mb = (read_sectors_delta * sector_size) / (1024 * 1024)
                write_mb = (write_sectors_delta * sector_size) / (1024 * 1024)
                
                self._prev_disk_stats = current_stats
                return {
                    'read_ops': max(0, read_ops_delta),
                    'write_ops': max(0, write_ops_delta),
                    'read_mb': max(0, read_mb),
                    'write_mb': max(0, write_mb)
                }
            else:
                self._prev_disk_stats = current_stats
                return {
                    'read_ops': 0,
                    'write_ops': 0,
                    'read_mb': 0,
                    'write_mb': 0
                }
        except:
            return None
    
    def get_average_stats(self) -> Dict[str, float]:
        """获取平均统计数据"""
        return {
            "cpu_usage_percent": sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0.0,
            "memory_usage_mb": sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0.0,
            "network_bandwidth_mbps": sum(self.network_usage) / len(self.network_usage) if self.network_usage else 0.0
        }
    
    def get_detailed_stats(self):
        """获取详细的系统统计信息"""
        stats = {
            "cpu": {
                "average": sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
                "max": max(self.cpu_usage) if self.cpu_usage else 0,
                "min": min(self.cpu_usage) if self.cpu_usage else 0,
                "samples": len(self.cpu_usage)
            },
            "memory": {
                "average": sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
                "max": max(self.memory_usage) if self.memory_usage else 0,
                "min": min(self.memory_usage) if self.memory_usage else 0,
                "samples": len(self.memory_usage)
            },
            "network": {
                "average_mbps": sum(self.network_usage) / len(self.network_usage) if self.network_usage else 0,
                "max_mbps": max(self.network_usage) if self.network_usage else 0,
                "total_mb": sum(self.network_usage) * (len(self.network_usage) if self.network_usage else 0) / 60,  # 假设每秒采样
                "samples": len(self.network_usage)
            },
            "disk_io": {
                "read_ops": sum([stat.get('read_ops', 0) for stat in self.disk_io_stats]),
                "write_ops": sum([stat.get('write_ops', 0) for stat in self.disk_io_stats]),
                "read_mb": sum([stat.get('read_mb', 0) for stat in self.disk_io_stats]),
                "write_mb": sum([stat.get('write_mb', 0) for stat in self.disk_io_stats]),
                "samples": len(self.disk_io_stats)
            }
        }
        return stats


class VMStoragePerformanceTest:
    """虚拟机存储性能测试主类"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.logger = Logger()
        self.monitor = SystemMonitor()
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
        # 创建测试目录
        os.makedirs(self.config.test_dir, exist_ok=True)
        
        self.logger.info(f"初始化虚拟机存储性能测试，测试目录: {self.config.test_dir}")
    
    def run_command(self, command: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """执行命令"""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=self.config.test_dir
            )
            return result
        except subprocess.TimeoutExpired:
            self.logger.error(f"命令执行超时: {' '.join(command)}")
            raise
        except Exception as e:
            self.logger.error(f"命令执行失败: {' '.join(command)}, 错误: {str(e)}")
            raise
    
    def parse_fio_output(self, output: str) -> Dict[str, float]:
        """解析fio输出"""
        metrics = {
            "throughput_mbps": 0.0,
            "iops": 0.0,
            "latency_avg_ms": 0.0,
            "latency_max_ms": 0.0,
            "latency_p95_ms": 0.0,
            "latency_p99_ms": 0.0
        }
        
        try:
            # 这里需要根据fio的实际输出格式来解析
            # 简化版解析逻辑
            lines = output.split('\n')
            for line in lines:
                if 'bw=' in line:
                    # 解析带宽
                    bw_part = line.split('bw=')[1].split(',')[0]
                    if 'MiB/s' in bw_part:
                        metrics["throughput_mbps"] = float(bw_part.replace('MiB/s', '').strip())
                elif 'iops=' in line:
                    # 解析IOPS
                    iops_part = line.split('iops=')[1].split(',')[0]
                    metrics["iops"] = float(iops_part.strip())
                elif 'lat (' in line:
                    # 解析延迟
                    if 'avg=' in line:
                        avg_part = line.split('avg=')[1].split(',')[0]
                        metrics["latency_avg_ms"] = float(avg_part.replace('msec', '').strip())
        except Exception as e:
            self.logger.warning(f"解析fio输出时出错: {str(e)}")
        
        return metrics
    
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始运行所有存储性能测试")
        
        try:
            # 1. 顺序读写性能测试
            self.run_sequential_tests()
            
            # 2. 随机读写性能测试
            self.run_random_tests()
            
            # 3. 并发性能测试
            self.run_concurrent_tests()
            
            # 4. 突发性能测试
            self.run_burst_tests()
            
            # 5. I/O对齐敏感度测试
            self.run_alignment_tests()
            
            # 生成测试报告
            self.generate_report()
            
        except Exception as e:
            self.logger.error(f"测试执行过程中出错: {str(e)}")
            raise
    
    def run_sequential_tests(self):
        """运行顺序读写测试"""
        self.logger.info("开始顺序读写性能测试")
        
        # 使用dd进行顺序写测试
        self._run_dd_sequential_tests()
        
        # 使用fio进行顺序读写测试
        self._run_fio_sequential_tests()
    
    def _run_dd_sequential_tests(self):
        """使用dd进行顺序读写测试"""
        self.logger.info("使用dd进行顺序读写测试")
        
        for block_size in self.config.sequential_block_sizes:
            # 顺序写测试
            self._run_dd_write_test(block_size)
            
            # 顺序读测试
            self._run_dd_read_test(block_size)
    
    def _run_dd_write_test(self, block_size: str):
        """dd顺序写测试"""
        test_file = os.path.join(self.config.test_dir, f"dd_write_{block_size}.dat")
        
        # 计算块数量
        size_bytes = self._parse_size_to_bytes(self.config.test_file_size)
        block_bytes = self._parse_size_to_bytes(block_size)
        count = size_bytes // block_bytes
        
        command = [
            "dd",
            f"if=/dev/zero",
            f"of={test_file}",
            f"bs={block_size}",
            f"count={count}",
            "conv=fdatasync"
        ]
        
        self.logger.info(f"执行dd写测试: {' '.join(command)}")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(command, timeout=600)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析dd输出获取性能数据
            throughput = self._parse_dd_output(result.stderr, size_bytes, duration)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"DD顺序写测试_{block_size}",
                test_type="sequential_write",
                parameters={"block_size": block_size, "file_size": self.config.test_file_size},
                throughput_mbps=throughput,
                duration=duration,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(f"DD写测试完成: {block_size}, 吞吐量: {throughput:.2f} MB/s")
            
        except Exception as e:
            self.logger.error(f"DD写测试失败: {str(e)}")
            self.monitor.stop_monitoring()
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _run_dd_read_test(self, block_size: str):
        """dd顺序读测试"""
        test_file = os.path.join(self.config.test_dir, f"dd_read_{block_size}.dat")
        
        # 先创建测试文件
        size_bytes = self._parse_size_to_bytes(self.config.test_file_size)
        block_bytes = self._parse_size_to_bytes(block_size)
        count = size_bytes // block_bytes
        
        # 创建文件
        create_command = [
            "dd",
            f"if=/dev/zero",
            f"of={test_file}",
            f"bs={block_size}",
            f"count={count}",
            "conv=fdatasync"
        ]
        
        try:
            self.run_command(create_command, timeout=600)
            
            # 清除缓存
            self.run_command(["sync"])
            self.run_command(["echo", "3", ">", "/proc/sys/vm/drop_caches"], timeout=30)
            
            # 读测试
            read_command = [
                "dd",
                f"if={test_file}",
                f"of=/dev/null",
                f"bs={block_size}",
                f"count={count}"
            ]
            
            self.logger.info(f"执行dd读测试: {' '.join(read_command)}")
            
            # 开始监控
            self.monitor.start_monitoring()
            start_time = time.time()
            
            result = self.run_command(read_command, timeout=600)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析dd输出获取性能数据
            throughput = self._parse_dd_output(result.stderr, size_bytes, duration)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"DD顺序读测试_{block_size}",
                test_type="sequential_read",
                parameters={"block_size": block_size, "file_size": self.config.test_file_size},
                throughput_mbps=throughput,
                duration=duration,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(f"DD读测试完成: {block_size}, 吞吐量: {throughput:.2f} MB/s")
            
        except Exception as e:
            self.logger.error(f"DD读测试失败: {str(e)}")
            self.monitor.stop_monitoring()
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _run_fio_sequential_tests(self):
        """使用fio进行顺序读写测试"""
        self.logger.info("使用fio进行顺序读写测试")
        
        for block_size in self.config.sequential_block_sizes:
            # 顺序写测试
            self._run_fio_sequential_test(block_size, "write")
            
            # 顺序读测试
            self._run_fio_sequential_test(block_size, "read")
            
            # 顺序读写混合测试
            self._run_fio_sequential_test(block_size, "readwrite")
    
    def _run_fio_sequential_test(self, block_size: str, rw_type: str):
        """fio顺序读写测试"""
        test_file = os.path.join(self.config.test_dir, f"fio_seq_{rw_type}_{block_size}.dat")
        
        # 构建fio命令
        fio_command = [
            "fio",
            f"--name=seq_{rw_type}_{block_size}",
            f"--filename={test_file}",
            f"--rw={rw_type}",
            f"--bs={block_size}",
            f"--size={self.config.test_file_size}",
            f"--runtime={self.config.runtime}",
            "--direct=1",
            "--ioengine=libaio",
            "--iodepth=1",
            "--group_reporting",
            "--output-format=json"
        ]
        
        self.logger.info(f"执行fio顺序{rw_type}测试: {block_size}")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=self.config.runtime + 60)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"FIO顺序{rw_type}测试_{block_size}",
                test_type=f"sequential_{rw_type}",
                parameters={"block_size": block_size, "rw_type": rw_type},
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(f"FIO顺序{rw_type}测试完成: {block_size}, 吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s")
            
        except Exception as e:
            self.logger.error(f"FIO顺序{rw_type}测试失败: {str(e)}")
            self.monitor.stop_monitoring()
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _parse_size_to_bytes(self, size_str: str) -> int:
        """解析大小字符串为字节数"""
        size_str = size_str.upper()
        if size_str.endswith('K'):
            return int(size_str[:-1]) * 1024
        elif size_str.endswith('M'):
            return int(size_str[:-1]) * 1024 * 1024
        elif size_str.endswith('G'):
            return int(size_str[:-1]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _parse_dd_output(self, output: str, size_bytes: int, duration: float) -> float:
        """解析dd输出获取吞吐量"""
        try:
            # dd输出通常在stderr中包含传输速度信息
            lines = output.split('\n')
            for line in lines:
                if 'bytes' in line and 'copied' in line:
                    # 从dd输出中提取速度信息
                    if 'MB/s' in line:
                        speed_part = line.split('MB/s')[0].split()[-1]
                        return float(speed_part)
                    elif 'GB/s' in line:
                        speed_part = line.split('GB/s')[0].split()[-1]
                        return float(speed_part) * 1024
            
            # 如果无法从输出解析，则根据大小和时间计算
            return (size_bytes / (1024 * 1024)) / duration
            
        except Exception:
            # 备用计算方法
            return (size_bytes / (1024 * 1024)) / duration
    
    def _parse_fio_json_output(self, output: str) -> Dict[str, float]:
        """解析fio JSON输出"""
        metrics = {
            "throughput_mbps": 0.0,
            "iops": 0.0,
            "latency_avg_ms": 0.0,
            "latency_max_ms": 0.0,
            "latency_p95_ms": 0.0,
            "latency_p99_ms": 0.0
        }
        
        try:
            data = json.loads(output)
            jobs = data.get('jobs', [])
            
            if jobs:
                job = jobs[0]
                
                # 读取性能数据
                if 'read' in job:
                    read_data = job['read']
                    metrics["throughput_mbps"] += read_data.get('bw', 0) / 1024  # KB/s to MB/s
                    metrics["iops"] += read_data.get('iops', 0)
                    
                    lat_data = read_data.get('lat_ns', {})
                    if lat_data:
                        metrics["latency_avg_ms"] = lat_data.get('mean', 0) / 1000000  # ns to ms
                        metrics["latency_max_ms"] = lat_data.get('max', 0) / 1000000
                        
                        percentiles = lat_data.get('percentile', {})
                        metrics["latency_p95_ms"] = percentiles.get('95.000000', 0) / 1000000
                        metrics["latency_p99_ms"] = percentiles.get('99.000000', 0) / 1000000
                
                # 写入性能数据
                if 'write' in job:
                    write_data = job['write']
                    metrics["throughput_mbps"] += write_data.get('bw', 0) / 1024  # KB/s to MB/s
                    metrics["iops"] += write_data.get('iops', 0)
                    
                    if metrics["latency_avg_ms"] == 0:  # 如果读取延迟为0，使用写入延迟
                        lat_data = write_data.get('lat_ns', {})
                        if lat_data:
                            metrics["latency_avg_ms"] = lat_data.get('mean', 0) / 1000000
                            metrics["latency_max_ms"] = lat_data.get('max', 0) / 1000000
                            
                            percentiles = lat_data.get('percentile', {})
                            metrics["latency_p95_ms"] = percentiles.get('95.000000', 0) / 1000000
                            metrics["latency_p99_ms"] = percentiles.get('99.000000', 0) / 1000000
                
        except Exception as e:
            self.logger.warning(f"解析fio JSON输出时出错: {str(e)}")
            # 尝试解析文本输出
            metrics = self.parse_fio_output(output)
        
        return metrics
    
    def run_random_tests(self):
        """运行随机读写测试"""
        self.logger.info("开始随机读写性能测试")
        
        # 遍历所有测试参数组合
        for block_size in self.config.random_block_sizes:
            for rw_ratio in self.config.read_write_ratios:
                for queue_depth in self.config.queue_depths:
                    for write_mode in self.config.write_modes:
                        self._run_fio_random_test(block_size, rw_ratio, queue_depth, write_mode)
    
    def _run_fio_random_test(self, block_size: str, rw_ratio: str, queue_depth: int, write_mode: str):
        """fio随机读写测试"""
        test_name = f"random_{block_size}_{rw_ratio}_{queue_depth}_{write_mode}"
        test_file = os.path.join(self.config.test_dir, f"fio_{test_name}.dat")
        
        # 解析读写比例
        read_percent, write_percent = map(int, rw_ratio.split(':'))
        
        # 确定读写模式
        if read_percent == 100:
            rw_type = "randread"
        elif write_percent == 100:
            rw_type = "randwrite"
        else:
            rw_type = "randrw"
        
        # 构建fio命令
        fio_command = [
            "fio",
            f"--name={test_name}",
            f"--filename={test_file}",
            f"--rw={rw_type}",
            f"--bs={block_size}",
            f"--size={self.config.test_file_size}",
            f"--runtime={self.config.runtime}",
            f"--iodepth={queue_depth}",
            "--ioengine=libaio",
            "--group_reporting",
            "--output-format=json",
            "--time_based"
        ]
        
        # 添加读写比例参数（仅对混合模式）
        if rw_type == "randrw":
            fio_command.append(f"--rwmixread={read_percent}")
        
        # 添加写模式参数
        if write_mode == "direct":
            fio_command.append("--direct=1")
        elif write_mode == "sync":
            fio_command.append("--sync=1")
        elif write_mode == "dsync":
            fio_command.append("--sync=1")
            fio_command.append("--fsync=1")
        
        self.logger.info(f"执行随机读写测试: {test_name}")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=self.config.runtime + 120)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"随机读写测试_{test_name}",
                test_type="random_rw",
                parameters={
                    "block_size": block_size,
                    "rw_ratio": rw_ratio,
                    "queue_depth": queue_depth,
                    "write_mode": write_mode,
                    "rw_type": rw_type
                },
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"随机读写测试完成: {test_name}, "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s, "
                f"平均延迟: {metrics.get('latency_avg_ms', 0):.2f} ms"
            )
            
        except Exception as e:
            self.logger.error(f"随机读写测试失败: {test_name}, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"随机读写测试_{test_name}",
                test_type="random_rw",
                parameters={
                    "block_size": block_size,
                    "rw_ratio": rw_ratio,
                    "queue_depth": queue_depth,
                    "write_mode": write_mode,
                    "rw_type": rw_type
                },
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _run_dd_random_tests(self):
        """使用dd进行随机读写测试（有限功能）"""
        self.logger.info("使用dd进行随机读写测试")
        
        # dd主要用于顺序操作，随机测试功能有限
        # 这里实现一些基本的随机写测试
        for block_size in ["4K", "64K", "1M"]:
            self._run_dd_random_write_test(block_size)
    
    def _run_dd_random_write_test(self, block_size: str):
        """dd随机写测试（模拟）"""
        test_file = os.path.join(self.config.test_dir, f"dd_random_{block_size}.dat")
        
        # 使用dd创建稀疏文件进行随机写入模拟
        size_bytes = self._parse_size_to_bytes(self.config.test_file_size)
        block_bytes = self._parse_size_to_bytes(block_size)
        
        # 创建多个小的随机写入操作
        num_operations = min(100, size_bytes // block_bytes // 10)
        
        self.logger.info(f"执行dd随机写测试: {block_size}, {num_operations}次操作")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        total_bytes = 0
        
        try:
            for i in range(num_operations):
                # 随机选择写入位置
                seek_blocks = (i * 13) % (size_bytes // block_bytes)  # 简单的伪随机
                
                command = [
                    "dd",
                    "if=/dev/zero",
                    f"of={test_file}",
                    f"bs={block_size}",
                    "count=1",
                    f"seek={seek_blocks}",
                    "conv=notrunc"
                ]
                
                result = self.run_command(command, timeout=30)
                total_bytes += block_bytes
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 计算性能指标
            throughput = (total_bytes / (1024 * 1024)) / duration
            iops = num_operations / duration
            avg_latency = (duration * 1000) / num_operations
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"DD随机写测试_{block_size}",
                test_type="dd_random_write",
                parameters={"block_size": block_size, "operations": num_operations},
                throughput_mbps=throughput,
                iops=iops,
                latency_avg_ms=avg_latency,
                duration=duration,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"DD随机写测试完成: {block_size}, "
                f"IOPS: {iops:.0f}, "
                f"吞吐量: {throughput:.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"DD随机写测试失败: {str(e)}")
            self.monitor.stop_monitoring()
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def run_concurrent_tests(self):
        """运行并发性能测试"""
        self.logger.info("开始并发性能测试")
        
        # 多线程并发测试
        self._run_multithreaded_tests()
        
        # 多进程并发测试
        self._run_multiprocess_tests()
        
        # 多实例并发测试
        self._run_multiinstance_tests()
    
    def _run_multithreaded_tests(self):
        """多线程并发测试"""
        self.logger.info("开始多线程并发测试")
        
        for thread_count in [2, 4, 8, 16]:
            if thread_count > self.config.max_threads:
                break
            self._run_threaded_fio_test(thread_count)
    
    def _run_threaded_fio_test(self, thread_count: int):
        """多线程fio测试"""
        test_name = f"multithreaded_{thread_count}"
        
        # 为每个线程创建独立的测试文件
        test_files = []
        for i in range(thread_count):
            test_file = os.path.join(self.config.test_dir, f"fio_thread_{i}_{test_name}.dat")
            test_files.append(test_file)
        
        # 构建fio命令（多job配置）
        fio_command = [
            "fio",
            f"--name={test_name}",
            "--rw=randrw",
            "--bs=4K",
            f"--size={self.config.test_file_size}",
            f"--runtime={self.config.runtime}",
            "--iodepth=32",
            "--ioengine=libaio",
            "--group_reporting",
            "--output-format=json",
            "--time_based",
            f"--numjobs={thread_count}",
            "--thread"
        ]
        
        # 添加文件名模式
        base_filename = os.path.join(self.config.test_dir, f"fio_thread_{test_name}")
        fio_command.extend([f"--filename_format={base_filename}.$jobnum.dat"])
        
        self.logger.info(f"执行多线程测试: {thread_count}个线程")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=self.config.runtime + 120)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"多线程并发测试_{thread_count}线程",
                test_type="concurrent_multithreaded",
                parameters={"thread_count": thread_count},
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"多线程测试完成: {thread_count}线程, "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"多线程测试失败: {thread_count}线程, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"多线程并发测试_{thread_count}线程",
                test_type="concurrent_multithreaded",
                parameters={"thread_count": thread_count},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件
        for i in range(thread_count):
            test_file = os.path.join(self.config.test_dir, f"fio_thread_{test_name}.{i}.dat")
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def _run_multiprocess_tests(self):
        """多进程并发测试"""
        self.logger.info("开始多进程并发测试")
        
        for process_count in [2, 4, 8]:
            if process_count > self.config.max_processes:
                break
            self._run_multiprocess_fio_test(process_count)
    
    def _run_multiprocess_fio_test(self, process_count: int):
        """多进程fio测试"""
        import multiprocessing
        import queue
        
        test_name = f"multiprocess_{process_count}"
        
        self.logger.info(f"执行多进程测试: {process_count}个进程")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        # 创建结果队列
        result_queue = multiprocessing.Queue()
        processes = []
        
        try:
            # 启动多个进程
            for i in range(process_count):
                process = multiprocessing.Process(
                    target=self._run_single_process_fio,
                    args=(i, test_name, result_queue)
                )
                process.start()
                processes.append(process)
            
            # 等待所有进程完成
            for process in processes:
                process.join(timeout=self.config.runtime + 60)
                if process.is_alive():
                    process.terminate()
                    process.join()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 收集所有进程的结果
            total_iops = 0
            total_throughput = 0
            total_latency = 0
            successful_processes = 0
            
            while not result_queue.empty():
                try:
                    proc_result = result_queue.get_nowait()
                    if proc_result and 'iops' in proc_result:
                        total_iops += proc_result.get('iops', 0)
                        total_throughput += proc_result.get('throughput_mbps', 0)
                        total_latency += proc_result.get('latency_avg_ms', 0)
                        successful_processes += 1
                except:
                    break
            
            # 计算平均延迟
            avg_latency = total_latency / successful_processes if successful_processes > 0 else 0
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"多进程并发测试_{process_count}进程",
                test_type="concurrent_multiprocess",
                parameters={"process_count": process_count, "successful_processes": successful_processes},
                iops=total_iops,
                throughput_mbps=total_throughput,
                latency_avg_ms=avg_latency,
                duration=duration,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"多进程测试完成: {process_count}进程, "
                f"IOPS: {total_iops:.0f}, "
                f"吞吐量: {total_throughput:.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"多进程测试失败: {process_count}进程, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 终止所有进程
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"多进程并发测试_{process_count}进程",
                test_type="concurrent_multiprocess",
                parameters={"process_count": process_count},
                error_message=str(e)
            )
            self.results.append(test_result)
    
    def _run_single_process_fio(self, process_id: int, test_name: str, result_queue):
        """单个进程的fio测试"""
        test_file = os.path.join(self.config.test_dir, f"fio_proc_{process_id}_{test_name}.dat")
        
        fio_command = [
            "fio",
            f"--name=proc_{process_id}",
            f"--filename={test_file}",
            "--rw=randrw",
            "--bs=4K",
            f"--size={self.config.test_file_size}",
            f"--runtime={self.config.runtime}",
            "--iodepth=16",
            "--ioengine=libaio",
            "--output-format=json",
            "--time_based"
        ]
        
        try:
            result = self.run_command(fio_command, timeout=self.config.runtime + 60)
            metrics = self._parse_fio_json_output(result.stdout)
            result_queue.put(metrics)
        except Exception as e:
            result_queue.put({"error": str(e)})
        finally:
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def _run_multiinstance_tests(self):
        """多实例并发测试（模拟多个虚拟机实例）"""
        self.logger.info("开始多实例并发测试")
        
        # 模拟2-4个虚拟机实例的并发负载
        for instance_count in [2, 3, 4]:
            self._run_multiinstance_fio_test(instance_count)
    
    def _run_multiinstance_fio_test(self, instance_count: int):
        """多实例fio测试"""
        test_name = f"multiinstance_{instance_count}"
        
        # 为每个实例创建独立的工作目录
        instance_dirs = []
        for i in range(instance_count):
            instance_dir = os.path.join(self.config.test_dir, f"instance_{i}")
            os.makedirs(instance_dir, exist_ok=True)
            instance_dirs.append(instance_dir)
        
        self.logger.info(f"执行多实例测试: {instance_count}个实例")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        # 构建fio命令（多实例配置）
        fio_command = [
            "fio",
            f"--name={test_name}",
            "--rw=randrw",
            "--bs=4K",
            f"--size={self.config.test_file_size}",
            f"--runtime={self.config.runtime}",
            "--iodepth=16",
            "--ioengine=libaio",
            "--group_reporting",
            "--output-format=json",
            "--time_based",
            f"--numjobs={instance_count}",
            "--new_group"
        ]
        
        # 为每个实例添加独立的文件
        for i in range(instance_count):
            test_file = os.path.join(instance_dirs[i], f"instance_{i}.dat")
            if i == 0:
                fio_command.extend([f"--filename={test_file}"])
            else:
                fio_command.extend([f"--filename={test_file}", "--stonewall"])
        
        try:
            result = self.run_command(fio_command, timeout=self.config.runtime + 120)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"多实例并发测试_{instance_count}实例",
                test_type="concurrent_multiinstance",
                parameters={"instance_count": instance_count},
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"多实例测试完成: {instance_count}实例, "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"多实例测试失败: {instance_count}实例, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"多实例并发测试_{instance_count}实例",
                test_type="concurrent_multiinstance",
                parameters={"instance_count": instance_count},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件和目录
        for instance_dir in instance_dirs:
            try:
                import shutil
                shutil.rmtree(instance_dir)
            except:
                pass
    
    def run_burst_tests(self):
        """运行突发性能测试"""
        self.logger.info("开始突发性能测试")
        
        # 短时突发吞吐量测试
        self._run_burst_throughput_tests()
        
        # 多文件并发访问测试
        self._run_multifile_tests()
    
    def _run_burst_throughput_tests(self):
        """短时突发吞吐量测试"""
        self.logger.info("开始短时突发吞吐量测试")
        
        # 使用dd进行短时突发测试
        self._run_dd_burst_tests()
        
        # 使用fio进行短时突发测试
        self._run_fio_burst_tests()
    
    def _run_dd_burst_tests(self):
        """dd短时突发测试"""
        burst_durations = [5, 10, 15]  # 秒
        block_sizes = ["1M", "4M", "8M"]
        
        for duration in burst_durations:
            for block_size in block_sizes:
                self._run_dd_burst_test(block_size, duration)
    
    def _run_dd_burst_test(self, block_size: str, duration: int):
        """单个dd突发测试"""
        test_name = f"dd_burst_{block_size}_{duration}s"
        test_file = os.path.join(self.config.test_dir, f"{test_name}.dat")
        
        # 计算在指定时间内能写入的块数（估算）
        block_bytes = self._parse_size_to_bytes(block_size)
        # 假设平均写入速度为100MB/s来估算count
        estimated_speed = 100 * 1024 * 1024  # 100MB/s
        estimated_count = max(1, (estimated_speed * duration) // block_bytes)
        
        command = [
            "dd",
            "if=/dev/zero",
            f"of={test_file}",
            f"bs={block_size}",
            f"count={estimated_count}",
            "oflag=direct"
        ]
        
        self.logger.info(f"执行dd突发测试: {block_size}, {duration}秒, {estimated_count}块")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(command, timeout=duration + 30)
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析dd输出
            metrics = self._parse_dd_output(result.stderr)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"DD突发测试_{test_name}",
                test_type="burst_dd",
                parameters={
                    "block_size": block_size,
                    "target_duration": duration,
                    "actual_duration": actual_duration,
                    "count": estimated_count
                },
                duration=actual_duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"DD突发测试完成: {test_name}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s, "
                f"实际耗时: {actual_duration:.2f}秒"
            )
            
        except Exception as e:
            self.logger.error(f"DD突发测试失败: {test_name}, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"DD突发测试_{test_name}",
                test_type="burst_dd",
                parameters={"block_size": block_size, "duration": duration},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _run_fio_burst_tests(self):
        """fio短时突发测试"""
        burst_durations = [5, 10, 15]  # 秒
        
        for duration in burst_durations:
            self._run_fio_burst_test(duration)
    
    def _run_fio_burst_test(self, duration: int):
        """单个fio突发测试"""
        test_name = f"fio_burst_{duration}s"
        test_file = os.path.join(self.config.test_dir, f"{test_name}.dat")
        
        # 构建fio命令
        fio_command = [
            "fio",
            f"--name={test_name}",
            f"--filename={test_file}",
            "--rw=write",
            "--bs=1M",
            f"--size={self.config.test_file_size}",
            f"--runtime={duration}",
            "--iodepth=32",
            "--ioengine=libaio",
            "--direct=1",
            "--group_reporting",
            "--output-format=json",
            "--time_based"
        ]
        
        self.logger.info(f"执行fio突发测试: {duration}秒")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=duration + 30)
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"FIO突发测试_{test_name}",
                test_type="burst_fio",
                parameters={
                    "target_duration": duration,
                    "actual_duration": actual_duration
                },
                duration=actual_duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"FIO突发测试完成: {test_name}, "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"FIO突发测试失败: {test_name}, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"FIO突发测试_{test_name}",
                test_type="burst_fio",
                parameters={"duration": duration},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _run_multifile_tests(self):
        """多文件并发访问测试"""
        self.logger.info("开始多文件并发访问测试")
        
        # 测试不同数量的文件并发访问
        file_counts = [1, 4, 8, 16, 32, 64]
        
        for file_count in file_counts:
            if file_count > self.config.max_files:
                break
            self._run_multifile_fio_test(file_count)
    
    def _run_multifile_fio_test(self, file_count: int):
        """多文件fio测试"""
        test_name = f"multifile_{file_count}"
        
        # 创建测试文件目录
        test_dir = os.path.join(self.config.test_dir, f"multifile_{file_count}")
        os.makedirs(test_dir, exist_ok=True)
        
        # 构建fio命令
        fio_command = [
            "fio",
            f"--name={test_name}",
            f"--directory={test_dir}",
            "--rw=randrw",
            "--bs=4K",
            f"--size={self.config.test_file_size}",
            f"--runtime={self.config.runtime}",
            "--iodepth=16",
            "--ioengine=libaio",
            "--group_reporting",
            "--output-format=json",
            "--time_based",
            f"--numfiles={file_count}",
            "--file_service_type=roundrobin",
            "--norandommap"
        ]
        
        self.logger.info(f"执行多文件测试: {file_count}个文件")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=self.config.runtime + 120)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"多文件并发测试_{file_count}文件",
                test_type="multifile",
                parameters={"file_count": file_count},
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"多文件测试完成: {file_count}文件, "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"多文件测试失败: {file_count}文件, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"多文件并发测试_{file_count}文件",
                test_type="multifile",
                parameters={"file_count": file_count},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件和目录
        try:
            import shutil
            shutil.rmtree(test_dir)
        except:
            pass
    
    def _run_database_simulation_test(self):
        """数据库多表场景模拟测试"""
        self.logger.info("开始数据库多表场景模拟测试")
        
        # 模拟数据库多表并发访问
        table_counts = [4, 8, 16]  # 模拟表数量
        
        for table_count in table_counts:
            self._run_database_multifile_test(table_count)
    
    def _run_database_multifile_test(self, table_count: int):
        """数据库多表文件测试"""
        test_name = f"db_simulation_{table_count}_tables"
        
        # 创建数据库模拟目录
        db_dir = os.path.join(self.config.test_dir, f"db_sim_{table_count}")
        os.makedirs(db_dir, exist_ok=True)
        
        # 构建fio命令（模拟数据库访问模式）
        fio_command = [
            "fio",
            f"--name={test_name}",
            f"--directory={db_dir}",
            "--rw=randrw",
            "--rwmixread=70",  # 70%读，30%写，模拟典型数据库负载
            "--bs=8K",  # 数据库典型块大小
            f"--size={self.config.test_file_size}",
            f"--runtime={self.config.runtime}",
            "--iodepth=8",
            "--ioengine=libaio",
            "--group_reporting",
            "--output-format=json",
            "--time_based",
            f"--numfiles={table_count}",
            "--file_service_type=random",  # 随机访问文件，模拟表访问
            "--random_distribution=zipf:1.2",  # 模拟热点数据访问
            "--norandommap"
        ]
        
        self.logger.info(f"执行数据库模拟测试: {table_count}个表")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=self.config.runtime + 120)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"数据库模拟测试_{table_count}表",
                test_type="database_simulation",
                parameters={"table_count": table_count},
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"数据库模拟测试完成: {table_count}表, "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"数据库模拟测试失败: {table_count}表, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"数据库模拟测试_{table_count}表",
                test_type="database_simulation",
                parameters={"table_count": table_count},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件和目录
        try:
            import shutil
            shutil.rmtree(db_dir)
        except:
            pass
    
    def run_alignment_tests(self):
        """运行I/O对齐敏感度测试"""
        self.logger.info("开始I/O对齐敏感度测试")
        
        # 测试不同对齐偏移量
        self._run_alignment_offset_tests()
        
        # 测试不同块大小的对齐敏感度
        self._run_alignment_blocksize_tests()
    
    def _run_alignment_offset_tests(self):
        """对齐偏移量测试"""
        self.logger.info("开始对齐偏移量测试")
        
        # 测试不同的偏移量
        offsets = self.config.alignment_offsets  # [0, 512, 1024, 2048, 4096]
        block_sizes = ["4K", "8K", "16K", "64K"]
        
        for block_size in block_sizes:
            for offset in offsets:
                self._run_alignment_offset_test(block_size, offset)
    
    def _run_alignment_offset_test(self, block_size: str, offset: int):
        """单个对齐偏移量测试"""
        test_name = f"alignment_{block_size}_offset_{offset}"
        test_file = os.path.join(self.config.test_dir, f"{test_name}.dat")
        
        # 使用fio进行对齐测试
        fio_command = [
            "fio",
            f"--name={test_name}",
            f"--filename={test_file}",
            "--rw=randwrite",
            f"--bs={block_size}",
            f"--size={self.config.test_file_size}",
            f"--runtime={min(30, self.config.runtime)}",  # 对齐测试时间较短
            "--iodepth=16",
            "--ioengine=libaio",
            "--direct=1",
            "--group_reporting",
            "--output-format=json",
            "--time_based",
            f"--offset={offset}",  # 设置偏移量
            "--norandommap"
        ]
        
        self.logger.info(f"执行对齐测试: {block_size}, 偏移量: {offset}字节")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=60)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"对齐测试_{test_name}",
                test_type="alignment_offset",
                parameters={
                    "block_size": block_size,
                    "offset": offset,
                    "alignment_type": "offset"
                },
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"对齐测试完成: {block_size}, 偏移{offset}, "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"延迟: {metrics.get('avg_latency_ms', 0):.2f}ms"
            )
            
        except Exception as e:
            self.logger.error(f"对齐测试失败: {test_name}, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"对齐测试_{test_name}",
                test_type="alignment_offset",
                parameters={"block_size": block_size, "offset": offset},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _run_alignment_blocksize_tests(self):
        """块大小对齐敏感度测试"""
        self.logger.info("开始块大小对齐敏感度测试")
        
        # 测试对齐和非对齐的块大小
        aligned_sizes = ["4K", "8K", "16K", "32K", "64K"]  # 对齐的块大小
        unaligned_sizes = ["3K", "5K", "12K", "20K", "48K"]  # 非对齐的块大小
        
        # 测试对齐的块大小
        for block_size in aligned_sizes:
            self._run_alignment_blocksize_test(block_size, True)
        
        # 测试非对齐的块大小
        for block_size in unaligned_sizes:
            self._run_alignment_blocksize_test(block_size, False)
    
    def _run_alignment_blocksize_test(self, block_size: str, is_aligned: bool):
        """单个块大小对齐测试"""
        alignment_type = "aligned" if is_aligned else "unaligned"
        test_name = f"blocksize_{alignment_type}_{block_size}"
        test_file = os.path.join(self.config.test_dir, f"{test_name}.dat")
        
        # 使用fio进行块大小对齐测试
        fio_command = [
            "fio",
            f"--name={test_name}",
            f"--filename={test_file}",
            "--rw=randrw",
            "--rwmixread=70",
            f"--bs={block_size}",
            f"--size={self.config.test_file_size}",
            f"--runtime={min(30, self.config.runtime)}",
            "--iodepth=16",
            "--ioengine=libaio",
            "--direct=1",
            "--group_reporting",
            "--output-format=json",
            "--time_based",
            "--norandommap"
        ]
        
        self.logger.info(f"执行块大小对齐测试: {block_size} ({alignment_type})")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(fio_command, timeout=60)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析fio JSON输出
            metrics = self._parse_fio_json_output(result.stdout)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"块大小对齐测试_{test_name}",
                test_type="alignment_blocksize",
                parameters={
                    "block_size": block_size,
                    "is_aligned": is_aligned,
                    "alignment_type": alignment_type
                },
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"块大小对齐测试完成: {block_size} ({alignment_type}), "
                f"IOPS: {metrics.get('iops', 0):.0f}, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"块大小对齐测试失败: {test_name}, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"块大小对齐测试_{test_name}",
                test_type="alignment_blocksize",
                parameters={"block_size": block_size, "is_aligned": is_aligned},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _run_sector_alignment_tests(self):
        """扇区对齐测试"""
        self.logger.info("开始扇区对齐测试")
        
        # 测试512字节和4K扇区对齐
        sector_sizes = [512, 4096]  # 512字节和4K扇区
        
        for sector_size in sector_sizes:
            self._run_sector_alignment_test(sector_size)
    
    def _run_sector_alignment_test(self, sector_size: int):
        """单个扇区对齐测试"""
        test_name = f"sector_alignment_{sector_size}"
        test_file = os.path.join(self.config.test_dir, f"{test_name}.dat")
        
        # 使用dd进行扇区对齐测试
        dd_command = [
            "dd",
            "if=/dev/zero",
            f"of={test_file}",
            f"bs={sector_size}",
            "count=10240",  # 固定数量的块
            "oflag=direct"
        ]
        
        self.logger.info(f"执行扇区对齐测试: {sector_size}字节扇区")
        
        # 开始监控
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            result = self.run_command(dd_command, timeout=60)
            end_time = time.time()
            duration = end_time - start_time
            
            # 停止监控
            self.monitor.stop_monitoring()
            stats = self.monitor.get_average_stats()
            
            # 解析dd输出
            metrics = self._parse_dd_output(result.stderr)
            
            # 记录测试结果
            test_result = TestResult(
                test_name=f"扇区对齐测试_{sector_size}字节",
                test_type="sector_alignment",
                parameters={
                    "sector_size": sector_size,
                    "alignment_type": "sector"
                },
                duration=duration,
                **metrics,
                **stats
            )
            
            self.results.append(test_result)
            self.logger.info(
                f"扇区对齐测试完成: {sector_size}字节, "
                f"吞吐量: {metrics.get('throughput_mbps', 0):.2f} MB/s"
            )
            
        except Exception as e:
            self.logger.error(f"扇区对齐测试失败: {test_name}, 错误: {str(e)}")
            self.monitor.stop_monitoring()
            
            # 记录失败结果
            test_result = TestResult(
                test_name=f"扇区对齐测试_{sector_size}字节",
                test_type="sector_alignment",
                parameters={"sector_size": sector_size},
                error_message=str(e)
            )
            self.results.append(test_result)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    def _analyze_performance_bottlenecks(self):
        """分析性能瓶颈"""
        self.logger.info("开始分析性能瓶颈")
        
        for result in self.results:
            if result.error_message:
                continue
                
            # 分析单个测试结果的性能瓶颈
            analysis = self._analyze_single_test_bottleneck(result)
            result.performance_analysis = analysis
    
    def _analyze_single_test_bottleneck(self, result: TestResult) -> PerformanceAnalysis:
        """分析单个测试的性能瓶颈"""
        bottlenecks = []
        
        # 延迟分析
        if result.latency_avg_ms:
            latency_score = self._calculate_latency_impact_score(result.latency_avg_ms, result.latency_p95_ms, result.latency_p99_ms)
            bottlenecks.append(PerformanceBottleneck(
                factor="延迟",
                impact_score=latency_score,
                description=f"平均延迟: {result.latency_avg_ms:.2f}ms, P95: {result.latency_p95_ms or 0:.2f}ms, P99: {result.latency_p99_ms or 0:.2f}ms",
                recommendation="优化存储配置或使用更快的存储设备" if latency_score > 70 else "当前延迟表现良好"
            ))
        
        # 吞吐量分析
        if result.throughput_mbps:
            throughput_score = self._calculate_throughput_impact_score(result.throughput_mbps, result.test_type)
            bottlenecks.append(PerformanceBottleneck(
                factor="吞吐量",
                impact_score=throughput_score,
                description=f"吞吐量: {result.throughput_mbps:.2f} MB/s",
                recommendation="增加并发度或优化I/O块大小" if throughput_score > 70 else "当前吞吐量表现良好"
            ))
        
        # IOPS分析
        if result.iops:
            iops_score = self._calculate_iops_impact_score(result.iops, result.test_type)
            bottlenecks.append(PerformanceBottleneck(
                factor="IOPS",
                impact_score=iops_score,
                description=f"IOPS: {result.iops:.0f}",
                recommendation="优化队列深度或使用SSD存储" if iops_score > 70 else "当前IOPS表现良好"
            ))
        
        # CPU使用率分析
        if result.cpu_usage_percent:
            cpu_score = self._calculate_cpu_impact_score(result.cpu_usage_percent)
            bottlenecks.append(PerformanceBottleneck(
                factor="CPU使用率",
                impact_score=cpu_score,
                description=f"CPU使用率: {result.cpu_usage_percent:.1f}%",
                recommendation="减少CPU密集型操作或升级CPU" if cpu_score > 70 else "当前CPU使用率正常"
            ))
        
        # 内存使用分析
        if result.memory_usage_mb:
            memory_score = self._calculate_memory_impact_score(result.memory_usage_mb)
            bottlenecks.append(PerformanceBottleneck(
                factor="内存使用",
                impact_score=memory_score,
                description=f"内存使用: {result.memory_usage_mb:.1f} MB",
                recommendation="增加系统内存或优化内存使用" if memory_score > 70 else "当前内存使用正常"
            ))
        
        # 网络带宽分析
        if result.network_bandwidth_mbps:
            network_score = self._calculate_network_impact_score(result.network_bandwidth_mbps)
            bottlenecks.append(PerformanceBottleneck(
                factor="网络带宽",
                impact_score=network_score,
                description=f"网络带宽: {result.network_bandwidth_mbps:.2f} MB/s",
                recommendation="升级网络带宽或优化网络配置" if network_score > 70 else "当前网络带宽充足"
            ))
        
        # I/O模式分析
        io_score = self._calculate_io_pattern_impact_score(result.parameters, result.test_type)
        bottlenecks.append(PerformanceBottleneck(
            factor="I/O模式",
            impact_score=io_score,
            description=self._get_io_pattern_description(result.parameters, result.test_type),
            recommendation="优化I/O模式或调整块大小" if io_score > 70 else "当前I/O模式配置合理"
        ))
        
        # 按影响分数排序
        bottlenecks.sort(key=lambda x: x.impact_score, reverse=True)
        
        # 获取Top 1和Top 3
        top1_bottleneck = bottlenecks[0] if bottlenecks else None
        top3_bottlenecks = bottlenecks[:3] if len(bottlenecks) >= 3 else bottlenecks
        
        # 计算整体性能分数
        overall_score = self._calculate_overall_performance_score(result, bottlenecks)
        
        # 生成分析总结
        summary = self._generate_analysis_summary(result, top1_bottleneck, top3_bottlenecks, overall_score)
        
        # 生成优化建议
        recommendations = self._generate_optimization_recommendations(top3_bottlenecks, result)
        
        return PerformanceAnalysis(
            top1_bottleneck=top1_bottleneck,
            top3_bottlenecks=top3_bottlenecks,
            overall_performance_score=overall_score,
            analysis_summary=summary,
            optimization_suggestions=recommendations
        )
    
    def _calculate_latency_impact_score(self, avg_latency: float, p95_latency: float = None, p99_latency: float = None) -> float:
        """计算延迟影响分数 (0-100, 越高表示延迟越严重)"""
        # 基于平均延迟的基础分数
        if avg_latency < 1:
            base_score = 10
        elif avg_latency < 5:
            base_score = 30
        elif avg_latency < 10:
            base_score = 50
        elif avg_latency < 50:
            base_score = 70
        else:
            base_score = 90
        
        # P95和P99延迟的额外惩罚
        penalty = 0
        if p95_latency and p95_latency > avg_latency * 2:
            penalty += 10
        if p99_latency and p99_latency > avg_latency * 5:
            penalty += 15
        
        return min(100, base_score + penalty)
    
    def _calculate_throughput_impact_score(self, throughput: float, test_type: str) -> float:
        """计算吞吐量影响分数 (0-100, 越高表示吞吐量越低)"""
        # 根据测试类型设定期望吞吐量基准
        if "sequential" in test_type:
            # 顺序读写期望较高吞吐量
            if throughput > 500:
                return 10
            elif throughput > 200:
                return 30
            elif throughput > 100:
                return 50
            elif throughput > 50:
                return 70
            else:
                return 90
        else:
            # 随机读写期望较低吞吐量
            if throughput > 100:
                return 10
            elif throughput > 50:
                return 30
            elif throughput > 20:
                return 50
            elif throughput > 10:
                return 70
            else:
                return 90
    
    def _calculate_iops_impact_score(self, iops: float, test_type: str) -> float:
        """计算IOPS影响分数 (0-100, 越高表示IOPS越低)"""
        if "random" in test_type:
            # 随机读写更关注IOPS
            if iops > 10000:
                return 10
            elif iops > 5000:
                return 30
            elif iops > 1000:
                return 50
            elif iops > 500:
                return 70
            else:
                return 90
        else:
            # 顺序读写IOPS要求较低
            if iops > 1000:
                return 10
            elif iops > 500:
                return 30
            elif iops > 100:
                return 50
            elif iops > 50:
                return 70
            else:
                return 90
    
    def _calculate_cpu_impact_score(self, cpu_usage: float) -> float:
        """计算CPU影响分数 (0-100, 越高表示CPU使用率越高)"""
        if cpu_usage < 20:
            return 10
        elif cpu_usage < 40:
            return 30
        elif cpu_usage < 60:
            return 50
        elif cpu_usage < 80:
            return 70
        else:
            return 90
    
    def _calculate_memory_impact_score(self, memory_usage: float) -> float:
        """计算内存影响分数 (0-100, 越高表示内存使用越多)"""
        # 假设系统总内存为8GB
        total_memory_gb = 8
        memory_usage_gb = memory_usage / 1024
        usage_percent = (memory_usage_gb / total_memory_gb) * 100
        
        if usage_percent < 20:
            return 10
        elif usage_percent < 40:
            return 30
        elif usage_percent < 60:
            return 50
        elif usage_percent < 80:
            return 70
        else:
            return 90
    
    def _calculate_network_impact_score(self, network_bandwidth: float) -> float:
        """计算网络影响分数 (0-100, 越高表示网络使用越多)"""
        if network_bandwidth < 10:
            return 10
        elif network_bandwidth < 50:
            return 30
        elif network_bandwidth < 100:
            return 50
        elif network_bandwidth < 500:
            return 70
        else:
            return 90
    
    def _calculate_io_pattern_impact_score(self, parameters: dict, test_type: str) -> float:
        """计算I/O模式影响分数"""
        score = 20  # 基础分数
        
        # 块大小影响
        block_size = parameters.get("block_size", "4k")
        if "k" in block_size:
            size_kb = int(block_size.replace("k", ""))
            if size_kb < 4:
                score += 20  # 小块大小增加延迟
            elif size_kb > 1024:
                score += 10  # 大块大小可能影响并发
        
        # 队列深度影响
        queue_depth = parameters.get("queue_depth", 1)
        if queue_depth == 1:
            score += 15  # 低队列深度限制并发性能
        elif queue_depth > 32:
            score += 10  # 过高队列深度可能增加延迟
        
        # 读写比例影响
        if "read_ratio" in parameters:
            read_ratio = parameters["read_ratio"]
            if read_ratio == 50:  # 混合读写最复杂
                score += 15
        
        # 对齐影响
        if not parameters.get("is_aligned", True):
            score += 25  # 未对齐严重影响性能
        
        return min(100, score)
    
    def _get_io_pattern_description(self, parameters: dict, test_type: str) -> str:
        """获取I/O模式描述"""
        desc_parts = []
        
        if "block_size" in parameters:
            desc_parts.append(f"块大小: {parameters['block_size']}")
        
        if "queue_depth" in parameters:
            desc_parts.append(f"队列深度: {parameters['queue_depth']}")
        
        if "read_ratio" in parameters:
            desc_parts.append(f"读写比例: {parameters['read_ratio']}% 读")
        
        if "is_aligned" in parameters:
            alignment = "对齐" if parameters["is_aligned"] else "未对齐"
            desc_parts.append(f"I/O对齐: {alignment}")
        
        if "pattern" in parameters:
            desc_parts.append(f"访问模式: {parameters['pattern']}")
        
        return ", ".join(desc_parts) if desc_parts else f"测试类型: {test_type}"
    
    def _calculate_overall_performance_score(self, result: TestResult, bottlenecks: list) -> float:
        """计算整体性能分数 (0-100, 越高表示性能越好)"""
        if not bottlenecks:
            return 50
        
        # 计算加权平均影响分数
        total_weight = 0
        weighted_impact = 0
        
        for bottleneck in bottlenecks:
            # 根据因素类型设定权重
            if bottleneck.factor in ["延迟", "IOPS", "吞吐量"]:
                weight = 3  # 核心性能指标权重更高
            elif bottleneck.factor in ["CPU使用率", "内存使用"]:
                weight = 2  # 系统资源权重中等
            else:
                weight = 1  # 其他因素权重较低
            
            weighted_impact += bottleneck.impact_score * weight
            total_weight += weight
        
        avg_impact = weighted_impact / total_weight if total_weight > 0 else 50
        
        # 性能分数 = 100 - 平均影响分数
        return max(0, 100 - avg_impact)
    
    def _generate_analysis_summary(self, result: TestResult, top1: PerformanceBottleneck, 
                                 top3: list, overall_score: float) -> str:
        """生成分析总结"""
        summary_parts = []
        
        # 整体性能评估
        if overall_score >= 80:
            performance_level = "优秀"
        elif overall_score >= 60:
            performance_level = "良好"
        elif overall_score >= 40:
            performance_level = "一般"
        else:
            performance_level = "较差"
        
        summary_parts.append(f"整体性能评级: {performance_level} ({overall_score:.1f}分)")
        
        # Top 1瓶颈分析
        if top1:
            summary_parts.append(f"主要瓶颈: {top1.factor} (影响分数: {top1.impact_score:.1f})")
        
        # Top 3瓶颈概述
        if len(top3) >= 3:
            top3_factors = [b.factor for b in top3]
            summary_parts.append(f"前三大瓶颈: {', '.join(top3_factors)}")
        
        return "; ".join(summary_parts)
    
    def _generate_optimization_recommendations(self, top3_bottlenecks: list, result: TestResult) -> list:
        """生成优化建议"""
        recommendations = []
        
        for bottleneck in top3_bottlenecks:
            if bottleneck.factor == "延迟":
                recommendations.append("考虑使用SSD存储或优化I/O队列深度以降低延迟")
            elif bottleneck.factor == "吞吐量":
                recommendations.append("增加块大小或使用并行I/O以提高吞吐量")
            elif bottleneck.factor == "IOPS":
                recommendations.append("优化随机访问模式或增加队列深度以提高IOPS")
            elif bottleneck.factor == "CPU使用率":
                recommendations.append("考虑减少CPU密集型操作或升级CPU性能")
            elif bottleneck.factor == "内存使用":
                recommendations.append("优化内存使用或增加系统内存容量")
            elif bottleneck.factor == "网络带宽":
                recommendations.append("优化网络配置或考虑本地存储以减少网络依赖")
            elif bottleneck.factor == "I/O模式":
                recommendations.append("优化I/O对齐、调整块大小或队列深度参数")
        
        # 去重并限制建议数量
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:5]  # 最多返回5条建议

    def generate_report(self):
        """生成测试报告"""
        self.logger.info("开始生成测试报告")
        
        if not self.results:
            self.logger.warning("没有测试结果可生成报告")
            return
        
        # 执行性能瓶颈分析
        self._analyze_performance_bottlenecks()
        
        # 生成详细报告
        report_data = self._collect_report_data()
        
        # 生成HTML报告
        html_report = self._generate_html_report(report_data)
        
        # 生成JSON报告
        json_report = self._generate_json_report(report_data)
        
        # 生成CSV报告
        csv_report = self._generate_csv_report(report_data)
        
        # 保存报告文件
        self._save_reports(html_report, json_report, csv_report)
        
        # 打印摘要
        self._print_summary(report_data)
    
    def _collect_report_data(self):
        """收集报告数据"""
        report_data = {
            "test_info": {
                "start_time": self.start_time,
                "end_time": time.time(),
                "total_duration": time.time() - self.start_time,
                "total_tests": len(self.results),
                "successful_tests": len([r for r in self.results if not r.error_message]),
                "failed_tests": len([r for r in self.results if r.error_message]),
                "test_directory": self.config.test_dir,
                "test_file_size": self.config.test_file_size
            },
            "results_by_type": {},
            "performance_summary": {},
            "detailed_results": []
        }
        
        # 按测试类型分组结果
        for result in self.results:
            test_type = result.test_type
            if test_type not in report_data["results_by_type"]:
                report_data["results_by_type"][test_type] = []
            report_data["results_by_type"][test_type].append(result)
            
            # 添加到详细结果
            result_dict = {
                "test_name": result.test_name,
                "test_type": result.test_type,
                "parameters": result.parameters,
                "duration": result.duration,
                "throughput_mbps": result.throughput_mbps,
                "iops": result.iops,
                "latency_avg_ms": result.latency_avg_ms,
                "latency_p95_ms": result.latency_p95_ms,
                "latency_p99_ms": result.latency_p99_ms,
                "cpu_usage_percent": result.cpu_usage_percent,
                "memory_usage_mb": result.memory_usage_mb,
                "network_bandwidth_mbps": result.network_bandwidth_mbps,
                "error_message": result.error_message
            }
            
            # 添加性能瓶颈分析信息
            if hasattr(result, 'performance_analysis') and result.performance_analysis:
                analysis = result.performance_analysis
                result_dict["performance_analysis"] = {
                    "overall_performance_score": analysis.overall_performance_score,
                    "analysis_summary": analysis.analysis_summary,
                    "top1_bottleneck": {
                        "factor": analysis.top1_bottleneck.factor,
                        "impact_score": analysis.top1_bottleneck.impact_score,
                        "description": analysis.top1_bottleneck.description,
                        "recommendation": analysis.top1_bottleneck.recommendation
                    } if analysis.top1_bottleneck else None,
                    "top3_bottlenecks": [
                        {
                            "factor": b.factor,
                            "impact_score": b.impact_score,
                            "description": b.description,
                            "recommendation": b.recommendation
                        } for b in analysis.top3_bottlenecks
                    ],
                    "optimization_suggestions": analysis.optimization_suggestions
                }
            
            report_data["detailed_results"].append(result_dict)
        
        # 生成性能摘要
        report_data["performance_summary"] = self._generate_performance_summary()
        
        # 生成整体性能瓶颈分析
        report_data["bottleneck_analysis"] = self._generate_overall_bottleneck_analysis()
        
        return report_data
    
    def _generate_performance_summary(self):
        """生成性能摘要"""
        summary = {
            "sequential_performance": {},
            "random_performance": {},
            "concurrent_performance": {},
            "burst_performance": {},
            "alignment_performance": {},
            "best_performers": {},
            "worst_performers": {}
        }
        
        # 顺序性能摘要
        seq_results = [r for r in self.results if r.test_type in ["sequential_dd", "sequential_fio"]]
        if seq_results:
            summary["sequential_performance"] = {
                "max_throughput_mbps": max([r.throughput_mbps or 0 for r in seq_results]),
                "avg_throughput_mbps": sum([r.throughput_mbps or 0 for r in seq_results]) / len(seq_results),
                "min_latency_ms": min([r.latency_avg_ms or float('inf') for r in seq_results if r.latency_avg_ms]),
                "test_count": len(seq_results)
            }
        
        # 随机性能摘要
        rand_results = [r for r in self.results if r.test_type == "random_fio"]
        if rand_results:
            summary["random_performance"] = {
                "max_iops": max([r.iops or 0 for r in rand_results]),
                "avg_iops": sum([r.iops or 0 for r in rand_results]) / len(rand_results),
                "min_latency_ms": min([r.latency_avg_ms or float('inf') for r in rand_results if r.latency_avg_ms]),
                "test_count": len(rand_results)
            }
        
        # 并发性能摘要
        conc_results = [r for r in self.results if "concurrent" in r.test_type or "multithread" in r.test_type]
        if conc_results:
            summary["concurrent_performance"] = {
                "max_total_iops": max([r.iops or 0 for r in conc_results]),
                "avg_total_iops": sum([r.iops or 0 for r in conc_results]) / len(conc_results),
                "test_count": len(conc_results)
            }
        
        # 突发性能摘要
        burst_results = [r for r in self.results if "burst" in r.test_type]
        if burst_results:
            summary["burst_performance"] = {
                "max_burst_throughput_mbps": max([r.throughput_mbps or 0 for r in burst_results]),
                "avg_burst_throughput_mbps": sum([r.throughput_mbps or 0 for r in burst_results]) / len(burst_results),
                "test_count": len(burst_results)
            }
        
        # 对齐性能摘要
        align_results = [r for r in self.results if "alignment" in r.test_type]
        if align_results:
            summary["alignment_performance"] = {
                "aligned_avg_iops": 0,
                "unaligned_avg_iops": 0,
                "alignment_impact_percent": 0,
                "test_count": len(align_results)
            }
            
            aligned_results = [r for r in align_results if r.parameters.get("is_aligned", True)]
            unaligned_results = [r for r in align_results if not r.parameters.get("is_aligned", True)]
            
            if aligned_results:
                summary["alignment_performance"]["aligned_avg_iops"] = sum([r.iops or 0 for r in aligned_results]) / len(aligned_results)
            if unaligned_results:
                summary["alignment_performance"]["unaligned_avg_iops"] = sum([r.iops or 0 for r in unaligned_results]) / len(unaligned_results)
            
            # 计算对齐影响
            if summary["alignment_performance"]["aligned_avg_iops"] > 0 and summary["alignment_performance"]["unaligned_avg_iops"] > 0:
                aligned_iops = summary["alignment_performance"]["aligned_avg_iops"]
                unaligned_iops = summary["alignment_performance"]["unaligned_avg_iops"]
                summary["alignment_performance"]["alignment_impact_percent"] = ((aligned_iops - unaligned_iops) / unaligned_iops) * 100
        
        # 最佳和最差性能者
        valid_results = [r for r in self.results if not r.error_message]
        if valid_results:
            # 按IOPS排序
            iops_sorted = sorted(valid_results, key=lambda x: x.iops or 0, reverse=True)
            summary["best_performers"]["highest_iops"] = {
                "test_name": iops_sorted[0].test_name,
                "iops": iops_sorted[0].iops,
                "parameters": iops_sorted[0].parameters
            }
            summary["worst_performers"]["lowest_iops"] = {
                "test_name": iops_sorted[-1].test_name,
                "iops": iops_sorted[-1].iops,
                "parameters": iops_sorted[-1].parameters
            }
            
            # 按吞吐量排序
            throughput_sorted = sorted(valid_results, key=lambda x: x.throughput_mbps or 0, reverse=True)
            summary["best_performers"]["highest_throughput"] = {
                "test_name": throughput_sorted[0].test_name,
                "throughput_mbps": throughput_sorted[0].throughput_mbps,
                "parameters": throughput_sorted[0].parameters
            }
            summary["worst_performers"]["lowest_throughput"] = {
                "test_name": throughput_sorted[-1].test_name,
                "throughput_mbps": throughput_sorted[-1].throughput_mbps,
                "parameters": throughput_sorted[-1].parameters
            }
            
            # 按延迟排序（越低越好）
            latency_sorted = sorted([r for r in valid_results if r.latency_avg_ms], key=lambda x: x.latency_avg_ms)
            if latency_sorted:
                summary["best_performers"]["lowest_latency"] = {
                    "test_name": latency_sorted[0].test_name,
                    "avg_latency_ms": latency_sorted[0].latency_avg_ms,
                    "parameters": latency_sorted[0].parameters
                }
                summary["worst_performers"]["highest_latency"] = {
                    "test_name": latency_sorted[-1].test_name,
                    "avg_latency_ms": latency_sorted[-1].latency_avg_ms,
                    "parameters": latency_sorted[-1].parameters
                }
        
        return summary
    
    def _generate_overall_bottleneck_analysis(self):
        """生成整体性能瓶颈分析"""
        analysis = {
            "overall_summary": {},
            "common_bottlenecks": {},
            "performance_distribution": {},
            "recommendations": []
        }
        
        # 获取所有有效的分析结果
        valid_analyses = []
        for result in self.results:
            if (hasattr(result, 'performance_analysis') and 
                result.performance_analysis and 
                not result.error_message):
                valid_analyses.append(result.performance_analysis)
        
        if not valid_analyses:
            return analysis
        
        # 整体性能分数统计
        overall_scores = [a.overall_performance_score for a in valid_analyses]
        analysis["overall_summary"] = {
            "total_tests_analyzed": len(valid_analyses),
            "avg_performance_score": sum(overall_scores) / len(overall_scores),
            "max_performance_score": max(overall_scores),
            "min_performance_score": min(overall_scores),
            "excellent_tests": len([s for s in overall_scores if s >= 80]),
            "good_tests": len([s for s in overall_scores if 60 <= s < 80]),
            "average_tests": len([s for s in overall_scores if 40 <= s < 60]),
            "poor_tests": len([s for s in overall_scores if s < 40])
        }
        
        # 统计常见瓶颈
        bottleneck_counts = {}
        all_bottlenecks = []
        
        for analysis_result in valid_analyses:
            for bottleneck in analysis_result.top3_bottlenecks:
                factor = bottleneck.factor
                if factor not in bottleneck_counts:
                    bottleneck_counts[factor] = {
                        "count": 0,
                        "total_impact": 0,
                        "high_impact_count": 0,
                        "medium_impact_count": 0,
                        "low_impact_count": 0
                    }
                
                bottleneck_counts[factor]["count"] += 1
                bottleneck_counts[factor]["total_impact"] += bottleneck.impact_score
                
                if bottleneck.impact_score >= 70:
                    bottleneck_counts[factor]["high_impact_count"] += 1
                elif bottleneck.impact_score >= 50:
                    bottleneck_counts[factor]["medium_impact_count"] += 1
                else:
                    bottleneck_counts[factor]["low_impact_count"] += 1
                
                all_bottlenecks.append(bottleneck)
        
        # 计算平均影响分数并排序
        for factor, data in bottleneck_counts.items():
            data["avg_impact_score"] = data["total_impact"] / data["count"]
            data["frequency_percent"] = (data["count"] / len(valid_analyses)) * 100
        
        # 按频率和影响分数排序，找出最常见的瓶颈
        sorted_bottlenecks = sorted(
            bottleneck_counts.items(),
            key=lambda x: (x[1]["frequency_percent"], x[1]["avg_impact_score"]),
            reverse=True
        )
        
        analysis["common_bottlenecks"] = {
            "top_bottleneck_factors": [
                {
                    "factor": factor,
                    "frequency_percent": data["frequency_percent"],
                    "avg_impact_score": data["avg_impact_score"],
                    "occurrence_count": data["count"],
                    "high_impact_count": data["high_impact_count"]
                }
                for factor, data in sorted_bottlenecks[:5]
            ],
            "most_critical_factor": sorted_bottlenecks[0][0] if sorted_bottlenecks else None,
            "total_unique_factors": len(bottleneck_counts)
        }
        
        # 性能分布分析
        analysis["performance_distribution"] = {
            "excellent_percent": (analysis["overall_summary"]["excellent_tests"] / len(valid_analyses)) * 100,
            "good_percent": (analysis["overall_summary"]["good_tests"] / len(valid_analyses)) * 100,
            "average_percent": (analysis["overall_summary"]["average_tests"] / len(valid_analyses)) * 100,
            "poor_percent": (analysis["overall_summary"]["poor_tests"] / len(valid_analyses)) * 100
        }
        
        # 生成整体优化建议
        recommendations = []
        
        # 基于最常见瓶颈的建议
        if sorted_bottlenecks:
            top_factor = sorted_bottlenecks[0][0]
            top_frequency = sorted_bottlenecks[0][1]["frequency_percent"]
            
            if top_frequency > 50:  # 超过50%的测试都有这个瓶颈
                if top_factor == "延迟":
                    recommendations.append(f"延迟是最主要的性能瓶颈(出现在{top_frequency:.1f}%的测试中)，建议优先考虑使用更快的存储设备或优化I/O队列配置")
                elif top_factor == "吞吐量":
                    recommendations.append(f"吞吐量限制是主要瓶颈(出现在{top_frequency:.1f}%的测试中)，建议增加并行度或优化块大小配置")
                elif top_factor == "IOPS":
                    recommendations.append(f"IOPS性能是主要瓶颈(出现在{top_frequency:.1f}%的测试中)，建议优化随机访问模式或增加队列深度")
                elif top_factor == "CPU使用率":
                    recommendations.append(f"CPU使用率过高是主要瓶颈(出现在{top_frequency:.1f}%的测试中)，建议优化CPU密集型操作或升级硬件")
        
        # 基于性能分布的建议
        poor_percent = analysis["performance_distribution"]["poor_percent"]
        if poor_percent > 30:
            recommendations.append(f"有{poor_percent:.1f}%的测试性能较差，建议全面检查存储配置和系统资源")
        elif poor_percent > 10:
            recommendations.append(f"有{poor_percent:.1f}%的测试性能不佳，建议针对性优化相关测试场景")
        
        # 基于整体性能分数的建议
        avg_score = analysis["overall_summary"]["avg_performance_score"]
        if avg_score < 40:
            recommendations.append("整体性能评分较低，建议进行全面的系统性能调优")
        elif avg_score < 60:
            recommendations.append("整体性能有改进空间，建议重点关注主要瓶颈因素")
        
        analysis["recommendations"] = recommendations[:10]  # 最多10条建议
        
        return analysis
    
    def _generate_html_report(self, report_data):
        """生成HTML报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>虚拟机存储性能测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #333; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .metric {{ display: flex; justify-content: space-between; margin: 5px 0; }}
        .metric-value {{ font-weight: bold; color: #007bff; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .performance-high {{ background-color: #d4edda; }}
        .performance-medium {{ background-color: #fff3cd; }}
        .performance-low {{ background-color: #f8d7da; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>虚拟机存储性能测试报告</h1>
        
        <div class="summary-card">
            <h3>测试概览</h3>
            <div class="metric"><span>开始时间:</span><span class="metric-value">{start_time}</span></div>
            <div class="metric"><span>结束时间:</span><span class="metric-value">{end_time}</span></div>
            <div class="metric"><span>总耗时:</span><span class="metric-value">{total_duration:.2f} 秒</span></div>
            <div class="metric"><span>总测试数:</span><span class="metric-value">{total_tests}</span></div>
            <div class="metric"><span>成功测试:</span><span class="metric-value success">{successful_tests}</span></div>
            <div class="metric"><span>失败测试:</span><span class="metric-value error">{failed_tests}</span></div>
            <div class="metric"><span>测试目录:</span><span class="metric-value">{test_directory}</span></div>
            <div class="metric"><span>测试文件大小:</span><span class="metric-value">{test_file_size}</span></div>
        </div>
        
        <h2>性能摘要</h2>
        <div class="summary-grid">
            {performance_cards}
        </div>
        
        <h2>最佳/最差性能</h2>
        <div class="summary-grid">
            {best_worst_cards}
        </div>
        
        <h2>性能瓶颈分析</h2>
        {bottleneck_analysis}
        
        <h2>详细测试结果</h2>
        <table>
            <thead>
                <tr>
                    <th>测试名称</th>
                    <th>测试类型</th>
                    <th>吞吐量 (MB/s)</th>
                    <th>IOPS</th>
                    <th>平均延迟 (ms)</th>
                    <th>CPU使用率 (%)</th>
                    <th>内存使用率 (%)</th>
                    <th>性能分数</th>
                    <th>主要瓶颈</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
                {detailed_results}
            </tbody>
        </table>
    </div>
</body>
</html>
        """
        
        # 格式化时间
        start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report_data["test_info"]["start_time"]))
        end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report_data["test_info"]["end_time"]))
        
        # 生成性能卡片
        performance_cards = self._generate_performance_cards(report_data["performance_summary"])
        
        # 生成最佳/最差性能卡片
        best_worst_cards = self._generate_best_worst_cards(report_data["performance_summary"])
        
        # 生成性能瓶颈分析内容
        bottleneck_analysis = self._generate_bottleneck_analysis_html(report_data.get("bottleneck_analysis", {}))
        
        # 生成详细结果表格
        detailed_results = self._generate_detailed_results_table(report_data["detailed_results"])
        
        return html_template.format(
            start_time=start_time,
            end_time=end_time,
            total_duration=report_data["test_info"]["total_duration"],
            total_tests=report_data["test_info"]["total_tests"],
            successful_tests=report_data["test_info"]["successful_tests"],
            failed_tests=report_data["test_info"]["failed_tests"],
            test_directory=report_data["test_info"]["test_directory"],
            test_file_size=report_data["test_info"]["test_file_size"],
            performance_cards=performance_cards,
            best_worst_cards=best_worst_cards,
            bottleneck_analysis=bottleneck_analysis,
            detailed_results=detailed_results
        )
    
    def _generate_performance_cards(self, summary):
        """生成性能摘要卡片"""
        cards = []
        
        # 顺序性能卡片
        if summary.get("sequential_performance"):
            seq = summary["sequential_performance"]
            cards.append(f"""
            <div class="summary-card">
                <h3>顺序读写性能</h3>
                <div class="metric"><span>最大吞吐量:</span><span class="metric-value">{seq.get('max_throughput_mbps', 0):.2f} MB/s</span></div>
                <div class="metric"><span>平均吞吐量:</span><span class="metric-value">{seq.get('avg_throughput_mbps', 0):.2f} MB/s</span></div>
                <div class="metric"><span>最低延迟:</span><span class="metric-value">{seq.get('min_latency_ms', 0):.2f} ms</span></div>
                <div class="metric"><span>测试数量:</span><span class="metric-value">{seq.get('test_count', 0)}</span></div>
            </div>
            """)
        
        # 随机性能卡片
        if summary.get("random_performance"):
            rand = summary["random_performance"]
            cards.append(f"""
            <div class="summary-card">
                <h3>随机读写性能</h3>
                <div class="metric"><span>最大IOPS:</span><span class="metric-value">{rand.get('max_iops', 0):.0f}</span></div>
                <div class="metric"><span>平均IOPS:</span><span class="metric-value">{rand.get('avg_iops', 0):.0f}</span></div>
                <div class="metric"><span>最低延迟:</span><span class="metric-value">{rand.get('min_latency_ms', 0):.2f} ms</span></div>
                <div class="metric"><span>测试数量:</span><span class="metric-value">{rand.get('test_count', 0)}</span></div>
            </div>
            """)
        
        # 并发性能卡片
        if summary.get("concurrent_performance"):
            conc = summary["concurrent_performance"]
            cards.append(f"""
            <div class="summary-card">
                <h3>并发性能</h3>
                <div class="metric"><span>最大并发IOPS:</span><span class="metric-value">{conc.get('max_total_iops', 0):.0f}</span></div>
                <div class="metric"><span>平均并发IOPS:</span><span class="metric-value">{conc.get('avg_total_iops', 0):.0f}</span></div>
                <div class="metric"><span>测试数量:</span><span class="metric-value">{conc.get('test_count', 0)}</span></div>
            </div>
            """)
        
        # 对齐性能卡片
        if summary.get("alignment_performance"):
            align = summary["alignment_performance"]
            cards.append(f"""
            <div class="summary-card">
                <h3>对齐敏感度</h3>
                <div class="metric"><span>对齐平均IOPS:</span><span class="metric-value">{align.get('aligned_avg_iops', 0):.0f}</span></div>
                <div class="metric"><span>非对齐平均IOPS:</span><span class="metric-value">{align.get('unaligned_avg_iops', 0):.0f}</span></div>
                <div class="metric"><span>对齐性能提升:</span><span class="metric-value">{align.get('alignment_impact_percent', 0):.1f}%</span></div>
                <div class="metric"><span>测试数量:</span><span class="metric-value">{align.get('test_count', 0)}</span></div>
            </div>
            """)
        
        return '\n'.join(cards)
    
    def _generate_best_worst_cards(self, summary):
        """生成最佳/最差性能卡片"""
        cards = []
        
        best = summary.get("best_performers", {})
        worst = summary.get("worst_performers", {})
        
        if best:
            cards.append(f"""
            <div class="summary-card performance-high">
                <h3>最佳性能</h3>
                {f'<div class="metric"><span>最高IOPS:</span><span class="metric-value">{best.get("highest_iops", {}).get("iops", 0):.0f} ({best.get("highest_iops", {}).get("test_name", "N/A")})</span></div>' if best.get("highest_iops") else ''}
                {f'<div class="metric"><span>最高吞吐量:</span><span class="metric-value">{best.get("highest_throughput", {}).get("throughput_mbps", 0):.2f} MB/s ({best.get("highest_throughput", {}).get("test_name", "N/A")})</span></div>' if best.get("highest_throughput") else ''}
                {f'<div class="metric"><span>最低延迟:</span><span class="metric-value">{best.get("lowest_latency", {}).get("avg_latency_ms", 0):.2f} ms ({best.get("lowest_latency", {}).get("test_name", "N/A")})</span></div>' if best.get("lowest_latency") else ''}
            </div>
            """)
        
        if worst:
            cards.append(f"""
            <div class="summary-card performance-low">
                <h3>最差性能</h3>
                {f'<div class="metric"><span>最低IOPS:</span><span class="metric-value">{worst.get("lowest_iops", {}).get("iops", 0):.0f} ({worst.get("lowest_iops", {}).get("test_name", "N/A")})</span></div>' if worst.get("lowest_iops") else ''}
                {f'<div class="metric"><span>最低吞吐量:</span><span class="metric-value">{worst.get("lowest_throughput", {}).get("throughput_mbps", 0):.2f} MB/s ({worst.get("lowest_throughput", {}).get("test_name", "N/A")})</span></div>' if worst.get("lowest_throughput") else ''}
                {f'<div class="metric"><span>最高延迟:</span><span class="metric-value">{worst.get("highest_latency", {}).get("avg_latency_ms", 0):.2f} ms ({worst.get("highest_latency", {}).get("test_name", "N/A")})</span></div>' if worst.get("highest_latency") else ''}
            </div>
            """)
        
        return '\n'.join(cards)
    
    def _generate_bottleneck_analysis_html(self, bottleneck_analysis):
        """生成性能瓶颈分析HTML内容"""
        if not bottleneck_analysis:
            return "<div class='summary-card'><h3>性能瓶颈分析</h3><p>暂无分析数据</p></div>"
        
        html_parts = []
        
        # 整体摘要
        overall = bottleneck_analysis.get("overall_summary", {})
        if overall:
            html_parts.append(f"""
            <div class="summary-card">
                <h3>整体性能摘要</h3>
                <div class="metric"><span>分析测试数:</span><span class="metric-value">{overall.get('total_tests_analyzed', 0)}</span></div>
                <div class="metric"><span>平均性能分数:</span><span class="metric-value">{overall.get('avg_performance_score', 0):.1f}</span></div>
                <div class="metric"><span>优秀测试:</span><span class="metric-value success">{overall.get('excellent_tests', 0)}</span></div>
                <div class="metric"><span>良好测试:</span><span class="metric-value">{overall.get('good_tests', 0)}</span></div>
                <div class="metric"><span>一般测试:</span><span class="metric-value warning">{overall.get('average_tests', 0)}</span></div>
                <div class="metric"><span>较差测试:</span><span class="metric-value error">{overall.get('poor_tests', 0)}</span></div>
            </div>
            """)
        
        # 常见瓶颈
        common = bottleneck_analysis.get("common_bottlenecks", {})
        if common and common.get("top_bottleneck_factors"):
            factors_html = ""
            for factor in common["top_bottleneck_factors"][:3]:  # 只显示前3个
                severity_class = "error" if factor["high_impact_count"] > 0 else "warning"
                factors_html += f"""
                <div class="metric">
                    <span>{factor['factor']}:</span>
                    <span class="metric-value {severity_class}">
                        {factor['frequency_percent']:.1f}% (影响分数: {factor['avg_impact_score']:.1f})
                    </span>
                </div>
                """
            
            html_parts.append(f"""
            <div class="summary-card">
                <h3>主要瓶颈因素</h3>
                <div class="metric"><span>最关键因素:</span><span class="metric-value error">{common.get('most_critical_factor', 'N/A')}</span></div>
                {factors_html}
            </div>
            """)
        
        # 性能分布
        distribution = bottleneck_analysis.get("performance_distribution", {})
        if distribution:
            html_parts.append(f"""
            <div class="summary-card">
                <h3>性能分布</h3>
                <div class="metric"><span>优秀 (≥80分):</span><span class="metric-value success">{distribution.get('excellent_percent', 0):.1f}%</span></div>
                <div class="metric"><span>良好 (60-79分):</span><span class="metric-value">{distribution.get('good_percent', 0):.1f}%</span></div>
                <div class="metric"><span>一般 (40-59分):</span><span class="metric-value warning">{distribution.get('average_percent', 0):.1f}%</span></div>
                <div class="metric"><span>较差 (<40分):</span><span class="metric-value error">{distribution.get('poor_percent', 0):.1f}%</span></div>
            </div>
            """)
        
        # 优化建议
        recommendations = bottleneck_analysis.get("recommendations", [])
        if recommendations:
            rec_html = ""
            for i, rec in enumerate(recommendations[:5], 1):  # 最多显示5条建议
                rec_html += f"<li>{rec}</li>"
            
            html_parts.append(f"""
            <div class="summary-card">
                <h3>优化建议</h3>
                <ol>{rec_html}</ol>
            </div>
            """)
        
        return '<div class="summary-grid">' + '\n'.join(html_parts) + '</div>'
    
    def _generate_detailed_results_table(self, detailed_results):
        """生成详细结果表格"""
        rows = []
        
        for result in detailed_results:
            status_class = "success" if not result["error_message"] else "error"
            status_text = "成功" if not result["error_message"] else "失败"
            
            # 获取性能分析信息
            performance_score = "N/A"
            main_bottleneck = "N/A"
            
            if result.get("performance_analysis"):
                analysis = result["performance_analysis"]
                performance_score = f"{analysis['overall_performance_score']:.1f}"
                if analysis.get('top1_bottleneck'):
                    main_bottleneck = f"{analysis['top1_bottleneck']['factor']} ({analysis['top1_bottleneck']['impact_score']:.1f})"
            
            # 根据性能分数设置样式
            score_class = "performance-high"
            if result.get("performance_analysis"):
                score = result["performance_analysis"]["overall_performance_score"]
                if score >= 80:
                    score_class = "performance-high"
                elif score >= 60:
                    score_class = "performance-medium"
                else:
                    score_class = "performance-low"
            
            rows.append(f"""
                <tr>
                    <td>{result["test_name"]}</td>
                    <td>{result["test_type"]}</td>
                    <td>{result["throughput_mbps"] or 0:.2f}</td>
                    <td>{result["iops"] or 0:.0f}</td>
                    <td>{result["latency_avg_ms"] or 0:.2f}</td>
                    <td>{result["cpu_usage_percent"] or 0:.1f}</td>
                    <td>{result["memory_usage_mb"] or 0:.1f}</td>
                    <td class="{score_class}">{performance_score}</td>
                    <td>{main_bottleneck}</td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
            """)
        
        return '\n'.join(rows)
    
    def _generate_json_report(self, report_data):
        """生成JSON报告"""
        import json
        return json.dumps(report_data, indent=2, ensure_ascii=False, default=str)
    
    def _generate_csv_report(self, report_data):
        """生成CSV报告"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        headers = [
            "测试名称", "测试类型", "持续时间(秒)", "吞吐量(MB/s)", "IOPS", 
            "平均延迟(ms)", "P95延迟(ms)", "P99延迟(ms)", "CPU使用率(%)", 
            "内存使用率(%)", "网络带宽(MB/s)", "性能分数", "主要瓶颈", 
            "Top1瓶颈因素", "Top1影响分数", "Top3瓶颈因素", "错误信息"
        ]
        writer.writerow(headers)
        
        # 写入数据行
        for result in report_data["detailed_results"]:
            # 获取性能瓶颈分析信息
            performance_analysis = result.get("performance_analysis", {})
            performance_score = performance_analysis.get("overall_performance_score", 0)
            
            # 获取Top 1瓶颈
            top1_bottleneck = ""
            top1_score = ""
            if performance_analysis.get("top1_bottleneck"):
                top1 = performance_analysis["top1_bottleneck"]
                top1_bottleneck = f"{top1['factor']} ({top1['description']})"
                top1_score = f"{top1['impact_score']:.2f}"
            
            # 获取Top 3瓶颈
            top3_bottlenecks = ""
            if performance_analysis.get("top3_bottlenecks") and len(performance_analysis["top3_bottlenecks"]) >= 3:
                top3_list = []
                for i, bottleneck in enumerate(performance_analysis["top3_bottlenecks"][:3]):
                    top3_list.append(f"Top{i+1}: {bottleneck['factor']}({bottleneck['impact_score']:.2f})")
                top3_bottlenecks = "; ".join(top3_list)
            
            # 主要瓶颈描述
            main_bottleneck = performance_analysis.get("analysis_summary", "未分析")
            
            row = [
                result["test_name"],
                result["test_type"],
                result["duration"] or 0,
                result["throughput_mbps"] or 0,
                result["iops"] or 0,
                result["latency_avg_ms"] or 0,
                result["latency_p95_ms"] or 0,
                result["latency_p99_ms"] or 0,
                result["cpu_usage_percent"] or 0,
                result["memory_usage_mb"] or 0,
                result["network_bandwidth_mbps"] or 0,
                f"{performance_score:.2f}",
                main_bottleneck,
                top1_bottleneck,
                top1_score,
                top3_bottlenecks,
                result["error_message"] or ""
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def _save_reports(self, html_report, json_report, csv_report):
        """保存报告文件"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # 创建报告目录
        report_dir = os.path.join(self.config.test_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # 保存HTML报告
        html_file = os.path.join(report_dir, f"storage_performance_report_{timestamp}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        self.logger.info(f"HTML报告已保存到: {html_file}")
        
        # 保存JSON报告
        json_file = os.path.join(report_dir, f"storage_performance_report_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(json_report)
        self.logger.info(f"JSON报告已保存到: {json_file}")
        
        # 保存CSV报告
        csv_file = os.path.join(report_dir, f"storage_performance_report_{timestamp}.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_report)
        self.logger.info(f"CSV报告已保存到: {csv_file}")
        
        return html_file, json_file, csv_file
    
    def _print_summary(self, report_data):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("虚拟机存储性能测试摘要")
        print("="*80)
        
        test_info = report_data["test_info"]
        print(f"测试开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(test_info['start_time']))}")
        print(f"测试结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(test_info['end_time']))}")
        print(f"总测试时长: {test_info['total_duration']:.2f} 秒")
        print(f"总测试数量: {test_info['total_tests']}")
        print(f"成功测试: {test_info['successful_tests']}")
        print(f"失败测试: {test_info['failed_tests']}")
        print(f"测试目录: {test_info['test_directory']}")
        print(f"测试文件大小: {test_info['test_file_size']}")
        
        summary = report_data["performance_summary"]
        
        # 顺序性能摘要
        if summary.get("sequential_performance"):
            seq = summary["sequential_performance"]
            print("\n顺序读写性能:")
            print(f"  最大吞吐量: {seq.get('max_throughput_mbps', 0):.2f} MB/s")
            print(f"  平均吞吐量: {seq.get('avg_throughput_mbps', 0):.2f} MB/s")
            print(f"  最低延迟: {seq.get('min_latency_ms', 0):.2f} ms")
        
        # 随机性能摘要
        if summary.get("random_performance"):
            rand = summary["random_performance"]
            print("\n随机读写性能:")
            print(f"  最大IOPS: {rand.get('max_iops', 0):.0f}")
            print(f"  平均IOPS: {rand.get('avg_iops', 0):.0f}")
            print(f"  最低延迟: {rand.get('min_latency_ms', 0):.2f} ms")
        
        # 并发性能摘要
        if summary.get("concurrent_performance"):
            conc = summary["concurrent_performance"]
            print("\n并发性能:")
            print(f"  最大并发IOPS: {conc.get('max_total_iops', 0):.0f}")
            print(f"  平均并发IOPS: {conc.get('avg_total_iops', 0):.0f}")
        
        # 对齐性能摘要
        if summary.get("alignment_performance"):
            align = summary["alignment_performance"]
            print("\n对齐敏感度:")
            print(f"  对齐平均IOPS: {align.get('aligned_avg_iops', 0):.0f}")
            print(f"  非对齐平均IOPS: {align.get('unaligned_avg_iops', 0):.0f}")
            print(f"  对齐性能提升: {align.get('alignment_impact_percent', 0):.1f}%")
        
        # 最佳性能
        best = summary.get("best_performers", {})
        if best:
            print("\n最佳性能:")
            if best.get("highest_iops"):
                print(f"  最高IOPS: {best['highest_iops']['iops']:.0f} ({best['highest_iops']['test_name']})")
            if best.get("highest_throughput"):
                print(f"  最高吞吐量: {best['highest_throughput']['throughput_mbps']:.2f} MB/s ({best['highest_throughput']['test_name']})")
            if best.get("lowest_latency"):
                print(f"  最低延迟: {best['lowest_latency']['avg_latency_ms']:.2f} ms ({best['lowest_latency']['test_name']})")
        
        print("\n" + "="*80)
        print("测试完成！详细报告已生成到 reports 目录")
        print("="*80)


def load_config(config_file: str) -> TestConfig:
    """加载配置文件"""
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return TestConfig(**config_data)
    else:
        return TestConfig()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="虚拟机存储性能测试工具")
    parser.add_argument(
        "--config", 
        default="config.json", 
        help="配置文件路径"
    )
    parser.add_argument(
        "--test-dir", 
        default="./test_data", 
        help="测试数据目录"
    )
    parser.add_argument(
        "--runtime", 
        type=int, 
        default=60, 
        help="测试运行时间（秒）"
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    if args.test_dir:
        config.test_dir = args.test_dir
    if args.runtime:
        config.runtime = args.runtime
    
    # 创建测试实例并运行
    test = VMStoragePerformanceTest(config)
    test.run_all_tests()


if __name__ == "__main__":
    main()