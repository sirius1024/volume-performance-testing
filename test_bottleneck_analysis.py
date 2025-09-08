#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能瓶颈分析功能测试脚本
"""

import sys
sys.path.append('.')
from vm_storage_performance_test import VMStoragePerformanceTest, TestConfig, TestResult, PerformanceBottleneck, PerformanceAnalysis
import time

def test_bottleneck_analysis():
    """测试性能瓶颈分析功能"""
    print("开始测试性能瓶颈分析功能...")
    
    # 创建测试配置
    config = TestConfig()
    config.test_dir = './test_data'
    config.runtime = 5
    config.test_file_size = '100M'
    
    # 创建测试实例
    test = VMStoragePerformanceTest(config)
    
    # 创建模拟测试结果
    mock_results = [
        TestResult(
            test_name="高延迟测试",
            test_type="sequential_dd",
            parameters={"block_size": "4K", "sync_mode": "sync"},
            throughput_mbps=10.5,
            iops=2688,
            latency_avg_ms=150.0,  # 高延迟
            latency_p95_ms=200.0,
            latency_p99_ms=250.0,
            cpu_usage_percent=25.0,
            memory_usage_mb=15.0,
            network_bandwidth_mbps=5.0,
            timestamp=time.time(),
            duration=5.0
        ),
        TestResult(
            test_name="高CPU使用率测试",
            test_type="random_fio",
            parameters={"block_size": "8K", "queue_depth": 32},
            throughput_mbps=50.0,
            iops=6400,
            latency_avg_ms=5.0,
            latency_p95_ms=8.0,
            latency_p99_ms=12.0,
            cpu_usage_percent=85.0,  # 高CPU使用率
            memory_usage_mb=30.0,
            network_bandwidth_mbps=25.0,
            timestamp=time.time(),
            duration=5.0
        ),
        TestResult(
            test_name="低吞吐量测试",
            test_type="sequential_fio",
            parameters={"block_size": "1M", "sync_mode": "dsync"},
            throughput_mbps=5.0,  # 低吞吐量
            iops=5,
            latency_avg_ms=20.0,
            latency_p95_ms=30.0,
            latency_p99_ms=40.0,
            cpu_usage_percent=15.0,
            memory_usage_mb=10.0,
            network_bandwidth_mbps=2.0,
            timestamp=time.time(),
            duration=5.0
        )
    ]
    
    # 设置模拟结果
    test.results = mock_results
    
    # 执行性能瓶颈分析
    print("\n执行性能瓶颈分析...")
    test._analyze_performance_bottlenecks()
    
    # 检查分析结果
    print("\n分析结果:")
    for i, result in enumerate(test.results):
        print(f"\n测试 {i+1}: {result.test_name}")
        if hasattr(result, 'performance_analysis') and result.performance_analysis:
            analysis = result.performance_analysis
            print(f"  整体性能分数: {analysis.overall_performance_score:.2f}")
            print(f"  分析总结: {analysis.analysis_summary}")
            
            if analysis.top1_bottleneck:
                print(f"  Top 1 瓶颈: {analysis.top1_bottleneck.factor} (影响分数: {analysis.top1_bottleneck.impact_score:.2f})")
                print(f"    描述: {analysis.top1_bottleneck.description}")
                print(f"    优化建议: {analysis.top1_bottleneck.recommendation}")
            
            if analysis.top3_bottlenecks:
                print(f"  Top 3 瓶颈:")
                for j, bottleneck in enumerate(analysis.top3_bottlenecks):
                    print(f"    {j+1}. {bottleneck.factor} (影响分数: {bottleneck.impact_score:.2f}, 建议: {bottleneck.recommendation})")
            
            if analysis.optimization_suggestions:
                print(f"  优化建议:")
                for j, suggestion in enumerate(analysis.optimization_suggestions):
                    print(f"    {j+1}. {suggestion}")
        else:
            print("  未找到性能分析结果")
    
    # 生成报告测试
    print("\n生成测试报告...")
    try:
        test.generate_report()
        print("报告生成成功！")
        
        # 检查报告文件是否生成
        import os
        report_dir = os.path.join(config.test_dir, "reports")
        if os.path.exists(report_dir):
            files = os.listdir(report_dir)
            html_files = [f for f in files if f.endswith('.html')]
            if html_files:
                print(f"HTML报告文件: {html_files[-1]}")
                return True
    except Exception as e:
        print(f"报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_bottleneck_analysis()
    if success:
        print("\n✅ 性能瓶颈分析功能测试通过！")
    else:
        print("\n❌ 性能瓶颈分析功能测试失败！")
        sys.exit(1)