import os
import subprocess

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
