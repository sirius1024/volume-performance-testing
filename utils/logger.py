import time
from datetime import datetime
import os

class Logger:
    """简单的日志记录器"""
    
    def __init__(self, log_file: str = "storage_test.log"):
        self.log_file = log_file
        self.start_time = time.time()
        
        # 确保日志文件目录存在
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                pass

        # 创建日志文件
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"存储性能测试日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
        except Exception as e:
            print(f"无法创建日志文件 {self.log_file}: {e}")
    
    def _log(self, level: str, message: str):
        """内部日志方法"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elapsed = time.time() - self.start_time
        log_entry = f"[{timestamp}] [{level}] [+{elapsed:.2f}s] {message}\n"
        
        # 写入文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass
        
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
