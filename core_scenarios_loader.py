import os
import json
import sys

def load_core_scenarios(path: str):
    """
    加载核心测试场景配置
    
    Args:
        path: 配置文件路径
        
    Returns:
        包含 'fio' 和 'dd' 场景列表的字典
    """
    if not os.path.exists(path):
        return {"fio": [], "dd": []}
        
    # 尝试作为 JSON 加载
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 验证并返回标准结构
        return {
            "fio": data.get("fio", []),
            "dd": data.get("dd", [])
        }
    except json.JSONDecodeError:
        # 如果不是有效的 JSON，检查是否是旧的 YAML 格式
        # 但我们不再支持手动解析，而是提示用户转换
        print(f"[WARN] 配置文件 {path} 格式无效或不是标准 JSON。")
        print(f"[HINT] 项目已完全迁移至 JSON 配置，请确保您的配置文件是有效的 JSON 格式。")
        return {"fio": [], "dd": []}
    except Exception as e:
        print(f"[ERROR] 加载配置文件 {path} 时出错: {str(e)}")
        return {"fio": [], "dd": []}
