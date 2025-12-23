from dataclasses import dataclass
from datetime import datetime

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
