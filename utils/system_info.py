import os
import platform
import subprocess
import shutil
from dataclasses import dataclass

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
