#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载模块
负责统一加载集群配置文件
"""

import json
import os
from typing import Dict, Any

def load_cluster_config(config_path: str = 'config/cluster.json') -> Dict[str, Any]:
    """
    加载集群配置文件
    
    Args:
        config_path: 配置文件路径，默认为 'config/cluster.json'
        
    Returns:
        包含配置信息的字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: 配置文件格式错误
    """
    # 如果是相对路径，尝试基于当前工作目录或项目根目录查找
    if not os.path.isabs(config_path):
        if not os.path.exists(config_path):
            # 尝试在项目根目录下查找（假设脚本可能在 tools 目录运行）
            root_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), config_path)
            if os.path.exists(root_path):
                config_path = root_path
            
            # 如果是 tools/config/cluster.json 这种情况（不太可能，但为了健壮性）
            # 或者尝试向上查找
            
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
