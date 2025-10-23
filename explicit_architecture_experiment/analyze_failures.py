#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_failures.py
分析分割失败的案例
"""

import json

def main():
    with open('java_projects_splitting_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== 显性架构分割失败案例 ===")
    failed = [r for r in data['explicit_results'] if not r['success']]
    
    for i, result in enumerate(failed, 1):
        print(f"\n失败案例 {i}:")
        print(f"  文件: {result['file'].split('\\')[-1]}")
        print(f"  原因: {result['reason']}")
        print(f"  行数: {result['lines']}")
    
    print(f"\n总计失败: {len(failed)} 个文件")
    print(f"失败率: {len(failed) / len(data['explicit_results']) * 100:.1f}%")

if __name__ == "__main__":
    main()
