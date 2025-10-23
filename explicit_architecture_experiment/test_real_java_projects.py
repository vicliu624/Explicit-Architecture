#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_real_java_projects.py
----------------------------------------------------
测试真实Java项目的分割效果

功能：
1. 测试MVC架构项目（ynyt-cloud-fund-service）
2. 测试显性架构项目（explict）
3. 对比两种架构的分割效果
4. 生成详细的分析报告
----------------------------------------------------
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import get_code_splitter

def find_java_files(directory: str, max_files: int = 20) -> List[str]:
    """查找目录下的Java文件"""
    java_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
                if len(java_files) >= max_files:
                    break
        if len(java_files) >= max_files:
            break
    return java_files

def test_java_file_splitting(file_path: str) -> Dict:
    """测试单个Java文件的分割效果"""
    print(f"\n=== 测试文件: {os.path.basename(file_path)} ===")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 3:
            return {
                'file': file_path,
                'success': False,
                'reason': 'File too short',
                'lines': len(lines)
            }
        
        # 获取Java分割器
        splitter = get_code_splitter('java')
        
        # 测试基本分割
        start_time = time.time()
        result = splitter.split_code(lines)
        split_time = time.time() - start_time
        
        if result:
            prefix, suffix = result
            total_length = len(prefix) + len(suffix)
            prefix_ratio = len(prefix) / total_length * 100
            suffix_ratio = len(suffix) / total_length * 100
            
            # 分析代码结构
            class_count = prefix.count('class ') + suffix.count('class ')
            method_count = prefix.count('public ') + suffix.count('public ')
            import_count = prefix.count('import ') + suffix.count('import ')
            
            return {
                'file': file_path,
                'success': True,
                'lines': len(lines),
                'split_time': split_time,
                'prefix_length': len(prefix),
                'suffix_length': len(suffix),
                'prefix_ratio': prefix_ratio,
                'suffix_ratio': suffix_ratio,
                'class_count': class_count,
                'method_count': method_count,
                'import_count': import_count,
                'prefix_preview': prefix[:300] + "..." if len(prefix) > 300 else prefix,
                'suffix_preview': suffix[:300] + "..." if len(suffix) > 300 else suffix
            }
        else:
            return {
                'file': file_path,
                'success': False,
                'reason': 'Splitter failed to split',
                'lines': len(lines),
                'split_time': split_time
            }
            
    except Exception as e:
        return {
            'file': file_path,
            'success': False,
            'reason': f'Error: {str(e)}',
            'lines': 0,
            'split_time': 0
        }

def analyze_architecture_differences(mvc_results: List[Dict], explicit_results: List[Dict]) -> Dict:
    """分析两种架构的分割差异"""
    
    def calculate_stats(results: List[Dict]) -> Dict:
        successful = [r for r in results if r['success']]
        if not successful:
            return {
                'success_rate': 0.0,
                'avg_split_time': 0.0,
                'avg_prefix_ratio': 0.0,
                'avg_suffix_ratio': 0.0,
                'avg_class_count': 0.0,
                'avg_method_count': 0.0,
                'avg_import_count': 0.0
            }
        
        return {
            'success_rate': len(successful) / len(results) * 100,
            'avg_split_time': sum(r['split_time'] for r in successful) / len(successful),
            'avg_prefix_ratio': sum(r['prefix_ratio'] for r in successful) / len(successful),
            'avg_suffix_ratio': sum(r['suffix_ratio'] for r in successful) / len(successful),
            'avg_class_count': sum(r['class_count'] for r in successful) / len(successful),
            'avg_method_count': sum(r['method_count'] for r in successful) / len(successful),
            'avg_import_count': sum(r['import_count'] for r in successful) / len(successful)
        }
    
    mvc_stats = calculate_stats(mvc_results)
    explicit_stats = calculate_stats(explicit_results)
    
    return {
        'mvc_architecture': mvc_stats,
        'explicit_architecture': explicit_stats,
        'comparison': {
            'success_rate_diff': explicit_stats['success_rate'] - mvc_stats['success_rate'],
            'split_time_diff': explicit_stats['avg_split_time'] - mvc_stats['avg_split_time'],
            'prefix_ratio_diff': explicit_stats['avg_prefix_ratio'] - mvc_stats['avg_prefix_ratio'],
            'class_count_diff': explicit_stats['avg_class_count'] - mvc_stats['avg_class_count'],
            'method_count_diff': explicit_stats['avg_method_count'] - mvc_stats['avg_method_count']
        }
    }

def main():
    """主测试函数"""
    print("=== 真实Java项目分割测试 ===")
    
    # 定义测试目录
    mvc_dir = r"C:\Users\vicliu\IdeaProjects\ynyt-cloud\ynyt-cloud-fund-service\src\main\java"
    explicit_dir = r"C:\Users\vicliu\Downloads\explict\main\java"
    
    # 检查目录是否存在
    if not os.path.exists(mvc_dir):
        print(f"MVC目录不存在: {mvc_dir}")
        return
    
    if not os.path.exists(explicit_dir):
        print(f"显性架构目录不存在: {explicit_dir}")
        return
    
    # 查找Java文件
    print(f"\n查找MVC架构Java文件...")
    mvc_files = find_java_files(mvc_dir, max_files=15)
    print(f"找到 {len(mvc_files)} 个MVC架构Java文件")
    
    print(f"\n查找显性架构Java文件...")
    explicit_files = find_java_files(explicit_dir, max_files=15)
    print(f"找到 {len(explicit_files)} 个显性架构Java文件")
    
    # 测试MVC架构文件
    print(f"\n=== 测试MVC架构文件 ===")
    mvc_results = []
    for file_path in mvc_files:
        result = test_java_file_splitting(file_path)
        mvc_results.append(result)
    
    # 测试显性架构文件
    print(f"\n=== 测试显性架构文件 ===")
    explicit_results = []
    for file_path in explicit_files:
        result = test_java_file_splitting(file_path)
        explicit_results.append(result)
    
    # 分析结果
    analysis = analyze_architecture_differences(mvc_results, explicit_results)
    
    print(f"\n=== 分割结果分析 ===")
    print(f"\nMVC架构统计:")
    mvc_stats = analysis['mvc_architecture']
    print(f"  成功率: {mvc_stats['success_rate']:.1f}%")
    print(f"  平均分割时间: {mvc_stats['avg_split_time']:.4f}秒")
    print(f"  平均前缀比例: {mvc_stats['avg_prefix_ratio']:.1f}%")
    print(f"  平均后缀比例: {mvc_stats['avg_suffix_ratio']:.1f}%")
    print(f"  平均类数量: {mvc_stats['avg_class_count']:.1f}")
    print(f"  平均方法数量: {mvc_stats['avg_method_count']:.1f}")
    print(f"  平均导入数量: {mvc_stats['avg_import_count']:.1f}")
    
    print(f"\n显性架构统计:")
    explicit_stats = analysis['explicit_architecture']
    print(f"  成功率: {explicit_stats['success_rate']:.1f}%")
    print(f"  平均分割时间: {explicit_stats['avg_split_time']:.4f}秒")
    print(f"  平均前缀比例: {explicit_stats['avg_prefix_ratio']:.1f}%")
    print(f"  平均后缀比例: {explicit_stats['avg_suffix_ratio']:.1f}%")
    print(f"  平均类数量: {explicit_stats['avg_class_count']:.1f}")
    print(f"  平均方法数量: {explicit_stats['avg_method_count']:.1f}")
    print(f"  平均导入数量: {explicit_stats['avg_import_count']:.1f}")
    
    print(f"\n对比分析:")
    comparison = analysis['comparison']
    print(f"  成功率差异: {comparison['success_rate_diff']:+.1f}%")
    print(f"  分割时间差异: {comparison['split_time_diff']:+.4f}秒")
    print(f"  前缀比例差异: {comparison['prefix_ratio_diff']:+.1f}%")
    print(f"  类数量差异: {comparison['class_count_diff']:+.1f}")
    print(f"  方法数量差异: {comparison['method_count_diff']:+.1f}")
    
    # 显示成功分割的详细信息
    print(f"\n=== MVC架构成功分割示例 ===")
    mvc_successful = [r for r in mvc_results if r['success']]
    for i, result in enumerate(mvc_successful[:3]):  # 显示前3个
        print(f"\n示例 {i+1}: {os.path.basename(result['file'])}")
        print(f"  行数: {result['lines']}")
        print(f"  分割时间: {result['split_time']:.4f}秒")
        print(f"  前缀比例: {result['prefix_ratio']:.1f}%")
        print(f"  后缀比例: {result['suffix_ratio']:.1f}%")
        print(f"  前缀预览: {result['prefix_preview']}")
        print(f"  后缀预览: {result['suffix_preview']}")
    
    print(f"\n=== 显性架构成功分割示例 ===")
    explicit_successful = [r for r in explicit_results if r['success']]
    for i, result in enumerate(explicit_successful[:3]):  # 显示前3个
        print(f"\n示例 {i+1}: {os.path.basename(result['file'])}")
        print(f"  行数: {result['lines']}")
        print(f"  分割时间: {result['split_time']:.4f}秒")
        print(f"  前缀比例: {result['prefix_ratio']:.1f}%")
        print(f"  后缀比例: {result['suffix_ratio']:.1f}%")
        print(f"  前缀预览: {result['prefix_preview']}")
        print(f"  后缀预览: {result['suffix_preview']}")
    
    # 保存详细结果到文件
    output_file = 'java_projects_splitting_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis': analysis,
            'mvc_results': mvc_results,
            'explicit_results': explicit_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
