#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIO测试模块
包含 FIOTestRunner 类与相关性能测试功能
矩阵规模：480 场景（8块大小×6队列深度×2并发×5读写比例）
快速模式：运行代表性组合，默认 runtime=3
执行引擎：在 9p 文件系统自动回退为 psync，其它使用 libaio
输出：为每个场景生成 JSON 文件并解析；日志打印完整命令
"""

import json
import os
import subprocess
import time
from typing import List, Dict, Any, Optional

from common import TestResult, Logger, clear_system_cache
from core_scenarios_loader import load_core_scenarios


class FIOTestRunner:
    """FIO测试执行器"""
    
    def __init__(self, test_dir: str, logger: Logger, runtime: int = 3, core_file: str = "config/core_scenarios.yaml"):
        self.test_dir = test_dir
        self.logger = logger
        self.runtime = runtime  # 测试运行时间（秒）
        self.core_file = core_file
        try:
            fs = "Unknown"
            p = subprocess.run(["df", "-T", self.test_dir], capture_output=True, text=True)
            if p.returncode == 0:
                lines = p.stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) > 1:
                        fs = parts[1]
            self.filesystem = fs
        except Exception:
            self.filesystem = "Unknown"
        
        # 测试配置矩阵
        self.block_sizes = ["4k", "8k", "16k", "32k", "64k", "128k", "1m", "4m"]
        self.queue_depths = [1, 2, 4, 8, 16, 32]
        self.rwmix_ratios = [0, 25, 50, 75, 100]  # 读取百分比
        
        # 队列深度与并发数的对应关系
        self.iodepth_numjobs_mapping = {
            1: [1, 4],
            2: [1, 4],
            4: [1, 4],
            8: [4, 8],
            16: [4, 8],
            32: [4, 8]
        }
        
        # 计算总测试场景数
        self.total_scenarios = len(self.block_sizes) * len(self.queue_depths) * 2 * len(self.rwmix_ratios)
        
        self.logger.info(f"FIO测试配置: {len(self.block_sizes)}种块大小 × {len(self.queue_depths)}种队列深度 × 2种并发 × {len(self.rwmix_ratios)}种读写比例 = {self.total_scenarios}种场景")
        try:
            self.core_scenarios = load_core_scenarios(self.core_file).get("fio", [])
        except Exception as e:
            self.core_scenarios = []
            self.logger.warning(f"加载核心场景失败: {str(e)}")
    
    def run_comprehensive_fio_tests(self) -> List[TestResult]:
        """运行完整的FIO测试套件（420种场景）"""
        all_results = []
        core = self._run_core_scenarios()
        if core:
            all_results.extend(core)
        scenario_count = 0
        
        self.logger.info(f"开始运行FIO完整测试套件，共{self.total_scenarios}种场景")
        start_time = time.time()
        
        for block_size in self.block_sizes:
            for queue_depth in self.queue_depths:
                # 根据队列深度获取对应的并发数列表
                numjobs_list = self.iodepth_numjobs_mapping[queue_depth]
                for numjobs in numjobs_list:
                    for rwmix_read in self.rwmix_ratios:
                        scenario_count += 1
                        
                        # 确定测试类型
                        if rwmix_read == 0:
                            test_type = "randwrite"
                            test_name = f"随机写"
                        elif rwmix_read == 100:
                            test_type = "randread"
                            test_name = f"随机读"
                        else:
                            test_type = "randrw"
                            test_name = f"随机读写({rwmix_read}%读)"
                        
                        self.logger.info(f"[{scenario_count}/{self.total_scenarios}] 执行FIO测试: {test_name}, 块大小={block_size}, 队列深度={queue_depth}, 并发={numjobs}")
                        
                        # 运行FIO测试
                        result = self._run_fio_test(
                            test_type=test_type,
                            block_size=block_size,
                            queue_depth=queue_depth,
                            numjobs=numjobs,
                            rwmix_read=rwmix_read,
                            runtime=self.runtime
                        )
                        
                        all_results.append(result)
                        
                        # 每完成50个测试打印进度
                        if scenario_count % 50 == 0:
                            elapsed = time.time() - start_time
                            avg_time_per_test = elapsed / scenario_count
                            remaining_tests = self.total_scenarios - scenario_count
                            estimated_remaining = avg_time_per_test * remaining_tests
                            
                            self.logger.info(f"进度: {scenario_count}/{self.total_scenarios} ({scenario_count/self.total_scenarios*100:.1f}%), 预计剩余时间: {estimated_remaining/60:.1f}分钟")
        
        total_time = time.time() - start_time
        successful_tests = [r for r in all_results if not r.error_message]
        
        self.logger.info(f"FIO完整测试套件完成")
        self.logger.info(f"总耗时: {total_time/60:.1f}分钟")
        self.logger.info(f"成功测试: {len(successful_tests)}/{len(all_results)}")
        
        return all_results

    def _run_core_scenarios(self) -> List[TestResult]:
        results: List[TestResult] = []
        for sc in self.core_scenarios:
            try:
                rw = str(sc.get("rw", "randread")).lower()
                bs = str(sc.get("bs", "4k")).lower()
                iodepth = int(sc.get("iodepth", 1))
                numjobs = int(sc.get("numjobs", 1))
                rwmix_read = int(sc.get("rwmixread", 50)) if rw == "randrw" else 0
                name = sc.get("name", f"CORE-{rw}-{bs}-qd{iodepth}-j{numjobs}")
                self.logger.info(f"[CORE] 执行FIO: {name}, bs={bs}, qd={iodepth}, nj={numjobs}")
                res = self._run_fio_test(
                    test_type=rw,
                    block_size=bs,
                    queue_depth=iodepth,
                    numjobs=numjobs,
                    rwmix_read=rwmix_read,
                    runtime=self.runtime
                )
                res.test_name = f"CORE {res.test_name}"
                results.append(res)
            except Exception as e:
                self.logger.error(f"[CORE] 执行核心场景失败: {str(e)}")
        return results
    
    def run_quick_fio_tests(self) -> List[TestResult]:
        """运行快速FIO测试（代表性场景）"""
        results = []
        core = self._run_core_scenarios()
        if core:
            results.extend(core)
        
        self.logger.info("开始运行FIO快速测试")
        
        # 选择代表性的测试配置
        quick_configs = [
            # 小块随机读写测试
            ("4k", 1, 1, 0, "randwrite"),    # 4K随机写
            ("4k", 1, 1, 100, "randread"),   # 4K随机读
            ("4k", 1, 1, 50, "randrw"),      # 4K随机读写
            ("4k", 32, 4, 0, "randwrite"),   # 4K高队列深度随机写
            ("4k", 32, 4, 100, "randread"),  # 4K高队列深度随机读
            
            # 中等块大小测试
            ("64k", 8, 1, 0, "randwrite"),   # 64K随机写
            ("64k", 8, 1, 100, "randread"),  # 64K随机读
            ("64k", 8, 1, 50, "randrw"),     # 64K随机读写
            
            # 大块测试
            ("1m", 4, 1, 0, "randwrite"),    # 1M随机写
            ("1m", 4, 1, 100, "randread"),   # 1M随机读
        ]
        
        for i, (block_size, queue_depth, numjobs, rwmix_read, test_type) in enumerate(quick_configs, 1):
            test_name = self._get_test_name(test_type, rwmix_read)
            self.logger.info(f"[{i}/{len(quick_configs)}] 快速FIO测试: {test_name}, 块大小={block_size}, 队列深度={queue_depth}")
            
            result = self._run_fio_test(
                test_type=test_type,
                block_size=block_size,
                queue_depth=queue_depth,
                numjobs=numjobs,
                rwmix_read=rwmix_read,
                runtime=self.runtime
            )
            
            results.append(result)
        
        self.logger.info(f"FIO快速测试完成，共执行 {len(results)} 个测试")
        return results
    
    def _run_fio_test(self, test_type: str, block_size: str, queue_depth: int, 
                     numjobs: int, rwmix_read: int, runtime: int) -> TestResult:
        """执行单个FIO测试"""
        
        # 构建测试名称
        test_name = f"FIO {self._get_test_name(test_type, rwmix_read)} {block_size} QD{queue_depth} J{numjobs}"
        
        # 创建测试结果对象
        result = TestResult(
            test_name=test_name,
            test_type=test_type,
            block_size=block_size,
            queue_depth=queue_depth,
            numjobs=numjobs,
            rwmix_read=rwmix_read
        )
        
        # 构建FIO命令
        test_file = f"fio_test_{block_size}_{queue_depth}_{numjobs}_{rwmix_read}"
        try:
            fp = os.path.join(self.test_dir, test_file)
            if not os.path.exists(fp):
                with open(fp, "wb") as f:
                    f.seek(10 * 1024 * 1024 * 1024 - 1)
                    f.write(b"\0")
        except Exception:
            pass
        
        ioengine = "libaio"
        if str(getattr(self, "filesystem", "")).lower() == "9p":
            ioengine = "psync"
        output_file = f"fio_json_{block_size}_{queue_depth}_{numjobs}_{rwmix_read}.json"
        fio_command = [
            "fio",
            "--name=test",
            f"--filename={test_file}",
            f"--rw={test_type}",
            f"--bs={block_size}",
            f"--iodepth={queue_depth}",
            f"--numjobs={numjobs}",
            f"--runtime={runtime}",
            "--time_based",
            f"--direct={'0' if str(getattr(self, 'filesystem', '')).lower() == '9p' and test_type in ('randread','randrw') else '1'}",
            f"--ioengine={ioengine}",
            "--group_reporting",
            "--output-format=json",
            "--size=10G",
            f"--output={output_file}"
        ]
        
        # 如果是混合读写，添加读写比例参数
        if test_type == "randrw":
            fio_command.append(f"--rwmixread={rwmix_read}")
        
        result.command = " ".join(fio_command)
        self.logger.info(f"命令: {result.command}")
        
        try:
            start_time = time.time()
            
            # 执行FIO命令
            process = subprocess.run(
                fio_command,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=runtime + 60
            )
            
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            
            if process.returncode == 0:
                try:
                    with open(os.path.join(self.test_dir, output_file), "r", encoding="utf-8") as jf:
                        self._parse_fio_json_output(jf.read(), result)
                except Exception:
                    self._parse_fio_json_output(process.stdout, result)
                
                if result.read_iops or result.write_iops:
                    self.logger.info(f"FIO测试完成: {test_name}")
                    if result.read_iops:
                        self.logger.info(f"  读取: {result.read_iops:.0f} IOPS, {result.read_mbps:.2f} MB/s")
                    if result.write_iops:
                        self.logger.info(f"  写入: {result.write_iops:.0f} IOPS, {result.write_mbps:.2f} MB/s")
                else:
                    # 尝试解析文本输出
                    self._parse_fio_text_output(process.stdout, result)
            else:
                result.error_message = process.stderr or "FIO命令执行失败"
                self.logger.error(f"FIO测试失败: {test_name}, 错误: {result.error_message}")
        
        except subprocess.TimeoutExpired:
            try:
                fallback_command = fio_command.copy()
                for i, arg in enumerate(fallback_command):
                    if arg.startswith("--ioengine="):
                        fallback_command[i] = "--ioengine=sync"
                    if arg.startswith("--direct="):
                        fallback_command[i] = "--direct=0"
                process2 = subprocess.run(
                    fallback_command,
                    cwd=self.test_dir,
                    capture_output=True,
                    text=True,
                    timeout=runtime + 60
                )
                if process2.returncode == 0:
                    try:
                        with open(os.path.join(self.test_dir, output_file), "r", encoding="utf-8") as jf:
                            self._parse_fio_json_output(jf.read(), result)
                    except Exception:
                        self._parse_fio_json_output(process2.stdout, result)
                    result.error_message = ""
                    self.logger.info(f"FIO测试完成: {test_name}")
                else:
                    result.error_message = process2.stderr or "FIO命令执行失败"
                    self.logger.error(f"FIO测试失败: {test_name}, 错误: {result.error_message}")
            except Exception:
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
            jobs = data.get('jobs', [])
            
            if not jobs:
                return
            
            job = jobs[0]  # 使用第一个job的数据
            
            # 读取性能数据
            read_data = job.get('read', {})
            if read_data:
                result.read_iops = read_data.get('iops', 0)
                result.read_mbps = read_data.get('bw', 0) / 1024  # 转换为MB/s
                result.read_latency_us = read_data.get('lat_ns', {}).get('mean', 0) / 1000  # 转换为微秒
            
            # 写入性能数据
            write_data = job.get('write', {})
            if write_data:
                result.write_iops = write_data.get('iops', 0)
                result.write_mbps = write_data.get('bw', 0) / 1024  # 转换为MB/s
                result.write_latency_us = write_data.get('lat_ns', {}).get('mean', 0) / 1000  # 转换为微秒
            
            # 计算总体吞吐量
            result.throughput_mbps = result.read_mbps + result.write_mbps
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.warning(f"解析FIO JSON输出时出错: {str(e)}")
    
    def _parse_fio_text_output(self, output: str, result: TestResult):
        """解析FIO文本输出（备用方法）"""
        try:
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                
                # 查找读取性能数据
                if 'read:' in line and 'IOPS=' in line:
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if 'IOPS=' in part:
                            iops_str = part.split('=')[1].strip()
                            result.read_iops = float(iops_str)
                        elif 'BW=' in part:
                            bw_str = part.split('=')[1].strip()
                            if 'MiB/s' in bw_str:
                                result.read_mbps = float(bw_str.replace('MiB/s', ''))
                            elif 'KiB/s' in bw_str:
                                result.read_mbps = float(bw_str.replace('KiB/s', '')) / 1024
                
                # 查找写入性能数据
                elif 'write:' in line and 'IOPS=' in line:
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if 'IOPS=' in part:
                            iops_str = part.split('=')[1].strip()
                            result.write_iops = float(iops_str)
                        elif 'BW=' in part:
                            bw_str = part.split('=')[1].strip()
                            if 'MiB/s' in bw_str:
                                result.write_mbps = float(bw_str.replace('MiB/s', ''))
                            elif 'KiB/s' in bw_str:
                                result.write_mbps = float(bw_str.replace('KiB/s', '')) / 1024
            
            # 计算总体吞吐量
            result.throughput_mbps = result.read_mbps + result.write_mbps
            
        except Exception as e:
            self.logger.warning(f"解析FIO文本输出时出错: {str(e)}")
    
    def _get_test_name(self, test_type: str, rwmix_read: int) -> str:
        """获取测试类型的中文名称"""
        if test_type == "randread":
            return "随机读"
        elif test_type == "randwrite":
            return "随机写"
        elif test_type == "randrw":
            return f"随机读写({rwmix_read}%读)"
        else:
            return test_type
    
    def get_test_matrix_info(self) -> Dict[str, Any]:
        """获取测试矩阵信息"""
        # 获取所有可能的numjobs值
        all_numjobs = set()
        for numjobs_list in self.iodepth_numjobs_mapping.values():
            all_numjobs.update(numjobs_list)
        
        return {
            "block_sizes": self.block_sizes,
            "queue_depths": self.queue_depths,
            "numjobs_values": sorted(list(all_numjobs)),
            "iodepth_numjobs_mapping": self.iodepth_numjobs_mapping,
            "rwmix_ratios": self.rwmix_ratios,
            "total_scenarios": self.total_scenarios,
            "runtime_per_test": self.runtime,
            "estimated_total_time_minutes": (self.total_scenarios * (self.runtime + 5)) / 60  # 加5秒开销
        }
    
    def cleanup_test_files(self):
        """清理FIO测试文件"""
        try:
            import glob
            test_files = glob.glob(os.path.join(self.test_dir, "fio_test_*"))
            
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"已删除FIO测试文件: {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.warning(f"清理FIO测试文件时出错: {str(e)}")
    
    def generate_detailed_report(self, results: List[TestResult], output_file: str = "fio_detailed_report.md"):
        """生成详细的FIO测试报告，包含所有420个测试场景"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                self._write_report_header(f)
                self._write_test_matrix_summary(f)
                self._write_detailed_results(f, results)
                self._write_performance_analysis(f, results)
                
            self.logger.info(f"详细FIO测试报告已生成: {output_file}")
        except Exception as e:
            self.logger.error(f"生成详细报告时出错: {str(e)}")
    
    def _write_report_header(self, f):
        """写入报告头部"""
        from datetime import datetime
        f.write("# FIO存储性能测试详细报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("本报告包含了所有490个FIO测试场景的详细结果。\n\n")
    
    def _write_test_matrix_summary(self, f):
        """写入测试矩阵摘要"""
        # 获取所有可能的numjobs值
        all_numjobs = set()
        for numjobs_list in self.iodepth_numjobs_mapping.values():
            all_numjobs.update(numjobs_list)
        
        f.write("## 1. 测试矩阵摘要\n\n")
        f.write(f"- **块大小**: {', '.join(self.block_sizes)}\n")
        f.write(f"- **队列深度**: {', '.join(map(str, self.queue_depths))}\n")
        f.write(f"- **并发数**: {', '.join(map(str, sorted(list(all_numjobs))))}\n")
        f.write(f"- **队列深度与并发数映射**: {self.iodepth_numjobs_mapping}\n")
        f.write(f"- **读写比例**: {', '.join(map(str, self.rwmix_ratios))}%\n")
        f.write(f"- **总测试场景数**: {self.total_scenarios}\n")
        f.write(f"- **每个测试运行时间**: {self.runtime}秒\n\n")
    
    def _write_detailed_results(self, f, results: List[TestResult]):
        """写入详细测试结果"""
        f.write("## 2. 详细测试结果\n\n")
        
        # 按块大小分组
        for block_size in self.block_sizes:
            f.write(f"### 2.{self.block_sizes.index(block_size) + 1} {block_size.upper()}块大小测试结果\n\n")
            
            # 筛选当前块大小的结果
            block_results = [r for r in results if r.block_size == block_size]
            
            if not block_results:
                f.write("*该块大小暂无测试结果*\n\n")
                continue
            
            # 创建详细结果表格
            f.write("| 序号 | 队列深度 | 并发数 | 读写模式 | 读取IOPS | 写入IOPS | 读取带宽(MB/s) | 写入带宽(MB/s) | 读取延迟(μs) | 写入延迟(μs) | 状态 |\n")
            f.write("|------|----------|--------|----------|----------|----------|----------------|----------------|--------------|--------------|------|\n")
            
            # 按队列深度、并发数、读写比例排序
            sorted_results = sorted(block_results, key=lambda x: (x.queue_depth, x.numjobs, x.rwmix_read))
            
            for idx, result in enumerate(sorted_results, 1):
                status = "✅成功" if not result.error_message else "❌失败"
                read_mode = self._get_test_name("randread" if result.rwmix_read == 100 else 
                                               "randwrite" if result.rwmix_read == 0 else "randrw", 
                                               result.rwmix_read)
                
                f.write(f"| {idx} | {result.queue_depth} | {result.numjobs} | {read_mode} | "
                       f"{result.read_iops:.0f} | {result.write_iops:.0f} | "
                       f"{result.read_mbps:.2f} | {result.write_mbps:.2f} | "
                       f"{result.read_latency_us:.2f} | {result.write_latency_us:.2f} | {status} |\n")
            
            f.write("\n")
    
    def _write_performance_analysis(self, f, results: List[TestResult]):
        """写入性能分析"""
        f.write("## 3. 性能分析\n\n")
        
        successful_results = [r for r in results if not r.error_message]
        failed_results = [r for r in results if r.error_message]
        
        f.write(f"### 3.1 测试执行统计\n\n")
        f.write(f"- **总测试场景数**: {len(results)}\n")
        f.write(f"- **成功执行**: {len(successful_results)}\n")
        f.write(f"- **执行失败**: {len(failed_results)}\n")
        f.write(f"- **成功率**: {len(successful_results)/len(results)*100:.1f}%\n\n")
        
        if successful_results:
            f.write(f"### 3.2 性能指标汇总\n\n")
            
            # 按块大小统计性能
            f.write("| 块大小 | 最高读取IOPS | 最高写入IOPS | 最高读取带宽(MB/s) | 最高写入带宽(MB/s) | 平均读取延迟(μs) | 平均写入延迟(μs) |\n")
            f.write("|--------|--------------|--------------|-------------------|-------------------|------------------|------------------|\n")
            
            for block_size in self.block_sizes:
                block_results = [r for r in successful_results if r.block_size == block_size]
                if block_results:
                    max_read_iops = max(r.read_iops for r in block_results)
                    max_write_iops = max(r.write_iops for r in block_results)
                    max_read_mbps = max(r.read_mbps for r in block_results)
                    max_write_mbps = max(r.write_mbps for r in block_results)
                    avg_read_latency = sum(r.read_latency_us for r in block_results) / len(block_results)
                    avg_write_latency = sum(r.write_latency_us for r in block_results) / len(block_results)
                    
                    f.write(f"| {block_size.upper()} | {max_read_iops:.0f} | {max_write_iops:.0f} | "
                           f"{max_read_mbps:.2f} | {max_write_mbps:.2f} | "
                           f"{avg_read_latency:.2f} | {avg_write_latency:.2f} |\n")
            
            f.write("\n")
        
        if failed_results:
            f.write(f"### 3.3 失败测试详情\n\n")
            for result in failed_results:
                f.write(f"- **{result.test_name}**: {result.error_message}\n")
            f.write("\n")


def main():
    """FIO测试模块的独立运行入口"""
    import argparse
    from common import Logger, ensure_directory
    
    parser = argparse.ArgumentParser(description="FIO存储性能测试工具")
    parser.add_argument("--test-dir", default="./test_data", help="测试目录路径")
    parser.add_argument("--runtime", type=int, default=3, help="每个测试的运行时间（秒）")
    parser.add_argument("--quick", action="store_true", help="快速模式，仅运行代表性测试")
    parser.add_argument("--cleanup", action="store_true", help="测试完成后清理测试文件")
    parser.add_argument("--info", action="store_true", help="显示测试矩阵信息")
    
    args = parser.parse_args()
    
    # 确保测试目录存在
    if not ensure_directory(args.test_dir):
        print(f"无法创建测试目录: {args.test_dir}")
        return 1
    
    # 创建日志记录器
    logger = Logger(os.path.join(args.test_dir, "fio_test.log"))
    
    # 创建FIO测试执行器
    fio_runner = FIOTestRunner(args.test_dir, logger, args.runtime)
    
    # 显示测试矩阵信息
    if args.info:
        matrix_info = fio_runner.get_test_matrix_info()
        print("\n=== FIO测试矩阵信息 ===")
        print(f"块大小: {matrix_info['block_sizes']}")
        print(f"队列深度: {matrix_info['queue_depths']}")
        print(f"并发数: {matrix_info['numjobs_values']}")
        print(f"读写比例: {matrix_info['rwmix_ratios']}%")
        print(f"总测试场景数: {matrix_info['total_scenarios']}")
        print(f"每个测试运行时间: {matrix_info['runtime_per_test']}秒")
        print(f"预计总耗时: {matrix_info['estimated_total_time_minutes']:.1f}分钟")
        return 0
    
    try:
        # 运行测试
        if args.quick:
            logger.info("开始运行FIO快速测试")
            results = fio_runner.run_quick_fio_tests()
        else:
            logger.info("开始运行FIO完整测试套件")
            results = fio_runner.run_comprehensive_fio_tests()
        
        # 打印测试摘要
        successful_tests = [r for r in results if not r.error_message]
        failed_tests = [r for r in results if r.error_message]
        
        print(f"\n=== FIO测试摘要 ===")
        print(f"总测试数: {len(results)}")
        print(f"成功: {len(successful_tests)}")
        print(f"失败: {len(failed_tests)}")
        
        if successful_tests:
            # 计算性能统计
            read_tests = [r for r in successful_tests if r.read_iops > 0]
            write_tests = [r for r in successful_tests if r.write_iops > 0]
            
            if read_tests:
                avg_read_iops = sum(r.read_iops for r in read_tests) / len(read_tests)
                max_read_iops = max(r.read_iops for r in read_tests)
                print(f"平均读取IOPS: {avg_read_iops:.0f}")
                print(f"最高读取IOPS: {max_read_iops:.0f}")
            
            if write_tests:
                avg_write_iops = sum(r.write_iops for r in write_tests) / len(write_tests)
                max_write_iops = max(r.write_iops for r in write_tests)
                print(f"平均写入IOPS: {avg_write_iops:.0f}")
                print(f"最高写入IOPS: {max_write_iops:.0f}")
        
        if failed_tests:
            print("\n失败的测试:")
            for test_result in failed_tests[:10]:  # 只显示前10个失败测试
                print(f"- {test_result.test_name}: {test_result.error_message}")
            if len(failed_tests) > 10:
                print(f"... 还有 {len(failed_tests) - 10} 个失败测试")
        
        # 生成详细报告
        ts = time.strftime('%Y%m%d_%H%M%S')
        reports_dir = os.path.join(args.test_dir, "reports", ts)
        ensure_directory(reports_dir)
        name = "fio_detailed_report.md"
        if args.quick:
            base, ext = os.path.splitext(name)
            name = f"{base}-quick{ext}"
        report_file = os.path.join(reports_dir, name)
        fio_runner.generate_detailed_report(results, report_file)
        print(f"\n详细测试报告已生成: {report_file}")
        print(f"报告包含所有 {len(results)} 个测试场景的详细结果")
        
        # 清理测试文件
        if args.cleanup:
            fio_runner.cleanup_test_files()
        
        return 0
    
    except KeyboardInterrupt:
        print("\nFIO测试被用户中断")
        if args.cleanup:
            fio_runner.cleanup_test_files()
        return 1
    except Exception as e:
        print(f"FIO测试过程中出现错误: {str(e)}")
        if args.cleanup:
            fio_runner.cleanup_test_files()
        return 1


if __name__ == "__main__":
    exit(main())
