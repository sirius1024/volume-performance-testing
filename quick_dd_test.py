#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速DD测试脚本 - 验证新增的块大小和oflag选项功能
"""

import os
import subprocess
import time
from typing import List

class QuickDDTest:
    def __init__(self, test_dir: str = "./quick_test_data"):
        self.test_dir = test_dir
        os.makedirs(self.test_dir, exist_ok=True)
    
    def run_quick_tests(self):
        """运行快速DD测试"""
        print("=== 快速DD测试开始 ===")
        
        # 测试新增的块大小（使用较小的文件大小以节省时间）
        block_sizes = ["64K", "32K", "16K", "8K"]
        
        print("\n1. 测试新增的块大小（direct模式）:")
        for block_size in block_sizes:
            self._test_block_size(block_size, "direct")
        
        print("\n2. 测试oflag=direct,dsync选项:")
        for block_size in ["32K", "16K"]:
            self._test_block_size(block_size, "direct,dsync")
        
        print("\n3. 测试oflag=dsync选项:")
        for block_size in ["32K", "16K"]:
            self._test_block_size(block_size, "dsync")
        
        print("\n=== 快速DD测试完成 ===")
    
    def _test_block_size(self, block_size: str, oflag: str):
        """测试指定块大小和oflag选项"""
        # 计算count值（总共写入100MB）
        size_map = {
            "64K": 1600,   # 64K * 1600 = 100MB
            "32K": 3200,   # 32K * 3200 = 100MB
            "16K": 6400,   # 16K * 6400 = 100MB
            "8K": 12800    # 8K * 12800 = 100MB
        }
        
        count = size_map.get(block_size, 1600)
        test_file = f"quick_test_{block_size.lower()}_{oflag.replace(',', '_')}"
        
        command = [
            "dd",
            "if=/dev/zero",
            f"of={test_file}",
            f"bs={block_size}",
            f"count={count}",
            f"oflag={oflag}"
        ]
        
        print(f"  测试: {block_size} 块大小, oflag={oflag}")
        
        try:
            start_time = time.time()
            
            process = subprocess.run(
                command,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=60  # 1分钟超时
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if process.returncode == 0:
                # 解析速度
                speed = self._parse_speed(process.stderr)
                print(f"    ✓ 成功: {speed:.2f} MB/s, 耗时: {duration:.2f}s")
            else:
                print(f"    ✗ 失败: {process.stderr.strip()}")
        
        except subprocess.TimeoutExpired:
            print(f"    ✗ 超时")
        except Exception as e:
            print(f"    ✗ 异常: {str(e)}")
    
    def _parse_speed(self, output: str) -> float:
        """解析DD输出中的速度"""
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if 'copied' in line and 'MB/s' in line:
                    parts = line.split(',')
                    for part in parts:
                        if 'MB/s' in part:
                            speed_str = part.strip().split()[0]
                            return float(speed_str)
                elif 'copied' in line and 'GB/s' in line:
                    parts = line.split(',')
                    for part in parts:
                        if 'GB/s' in part:
                            speed_str = part.strip().split()[0]
                            return float(speed_str) * 1024
        except:
            pass
        return 0.0
    
    def cleanup(self):
        """清理测试文件"""
        try:
            import glob
            test_files = glob.glob(os.path.join(self.test_dir, "quick_test_*"))
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"已删除: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"清理文件时出错: {str(e)}")

if __name__ == "__main__":
    test = QuickDDTest()
    try:
        test.run_quick_tests()
    finally:
        print("\n清理测试文件...")
        test.cleanup()