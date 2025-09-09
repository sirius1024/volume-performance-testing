#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具模块
包含共享的数据结构、日志记录器和系统信息收集器
"""

import os
import platform
import subprocess
import shutil
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemInfo:
    """系统信息数据类"""
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
    """测试结果数据类"""
    test_name: str
    test_type: str
    command: str = ""
    block_size: str = ""
    file_size: str = ""
    duration_seconds: float = 0.0
    throughput_mbps: float = 0.0
    iops: float = 0.0
    latency_avg_us: float = 0.0
    latency_p95_us: float = 0.0
    latency_p99_us: float = 0.0
    error_message: str = ""
    timestamp: str = ""
    
    # FIO测试专用字段
    queue_depth: int = 0
    numjobs: int = 0
    rwmix_read: int = 0
    read_iops: float = 0.0
    write_iops: float = 0.0
    read_mbps: float = 0.0
    write_mbps: float = 0.0
    read_latency_us: float = 0.0
    write_latency_us: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class Logger:
    """简单的日志记录器"""
    
    def __init__(self, log_file: str = "storage_test.log"):
        self.log_file = log_file
        self.start_time = time.time()
        
        # 创建日志文件
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"存储性能测试日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
    
    def _log(self, level: str, message: str):
        """内部日志方法"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elapsed = time.time() - self.start_time
        log_entry = f"[{timestamp}] [{level}] [+{elapsed:.2f}s] {message}\n"
        
        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # 输出到控制台
        print(f"[{level}] {message}")
    
    def info(self, message: str):
        """信息日志"""
        self._log("INFO", message)
    
    def warning(self, message: str):
        """警告日志"""
        self._log("WARN", message)
    
    def error(self, message: str):
        """错误日志"""
        self._log("ERROR", message)
    
    def debug(self, message: str):
        """调试日志"""
        self._log("DEBUG", message)


class SystemInfoCollector:
    """系统信息收集器"""
    
    def __init__(self):
        pass
    
    def collect_system_info(self) -> SystemInfo:
        """收集系统信息"""
        info = SystemInfo()
        
        try:
            # CPU信息
            info.cpu_model = self._get_cpu_model()
            info.cpu_cores = os.cpu_count() or 0
            
            # 内存信息
            info.memory_total_gb = self._get_memory_info()
            
            # 操作系统信息
            info.os_name = platform.system()
            info.os_version = platform.release()
            info.kernel_version = platform.version()
            
            # 存储信息
            info.storage_type = self._get_storage_type()
            info.filesystem = self._get_filesystem_type()
            
            # 磁盘容量信息
            disk_info = self._get_disk_info()
            info.disk_capacity_gb = disk_info['total']
            info.available_space_gb = disk_info['available']
            
        except Exception as e:
            print(f"收集系统信息时出错: {str(e)}")
        
        return info
    
    def _get_cpu_model(self) -> str:
        """获取CPU型号"""
        try:
            if platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            return line.split(':')[1].strip()
            return platform.processor() or "Unknown"
        except:
            return "Unknown"
    
    def _get_memory_info(self) -> float:
        """获取内存信息（GB）"""
        try:
            if platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal' in line:
                            # 从KB转换为GB
                            kb = int(line.split()[1])
                            return kb / 1024 / 1024
            return 0.0
        except:
            return 0.0
    
    def _get_storage_type(self) -> str:
        """获取存储类型"""
        try:
            # 尝试检测是否为SSD
            result = subprocess.run(['lsblk', '-d', '-o', 'name,rota'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过标题行
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == '0':
                        return "SSD"
                return "HDD"
            return "Unknown"
        except:
            return "Unknown"
    
    def _get_filesystem_type(self) -> str:
        """获取文件系统类型"""
        try:
            result = subprocess.run(['df', '-T', '.'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) > 1:
                        return parts[1]
            return "Unknown"
        except:
            return "Unknown"
    
    def _get_disk_info(self) -> dict:
        """获取磁盘容量信息"""
        try:
            total, used, free = shutil.disk_usage('.')
            return {
                'total': total / (1024**3),  # 转换为GB
                'used': used / (1024**3),
                'available': free / (1024**3)
            }
        except:
            return {'total': 0.0, 'used': 0.0, 'available': 0.0}


def format_bytes(bytes_value: float) -> str:
    """格式化字节数为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_duration(seconds: float) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}小时"


def ensure_directory(directory: str) -> bool:
    """确保目录存在"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败 {directory}: {str(e)}")
        return False


def clear_system_cache():
    """清除系统缓存"""
    try:
        subprocess.run(['sync'], check=True)
        with open('/proc/sys/vm/drop_caches', 'w') as f:
            f.write('3')
        return True
    except Exception as e:
        print(f"清除缓存失败: {str(e)}")
        return False