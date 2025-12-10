#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成模块
负责生成综合测试报告
"""

import time
import os
import json
from typing import List, Optional
from models.result import TestResult
from utils.logger import Logger

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
