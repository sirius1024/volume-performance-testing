#!/usr/bin/env python3
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core_scenarios_loader import load_core_scenarios


def main():
    src = os.path.join("config", "core_scenarios.yaml")
    dst = os.path.join("config", "core_scenarios.json")
    data = load_core_scenarios(src)
    os.makedirs("config", exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "description": "核心业务场景（FIO/DD）",
            "fio": data.get("fio", []),
            "dd": data.get("dd", []),
        }, f, ensure_ascii=False, indent=2)
    print(dst)


if __name__ == "__main__":
    main()

