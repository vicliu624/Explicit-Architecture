#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_multi_level_splitting.py
----------------------------------------------------
测试多层分割功能

功能：
1. 测试文件级、类级、方法级分割
2. 验证分割质量和效果
3. 生成多层分割报告
----------------------------------------------------
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import get_code_splitter

def test_multi_level_splitting(file_path: str) -> Dict:
    """测试单个文件的多层分割效果"""
    print(f"\n=== 测试多层分割: {os.path.basename(file_path)} ===")
    
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
        
        # 测试多层分割
        multi_results = splitter.split_code_multi_level(lines)
        
        if multi_results:
            return {
                'file': file_path,
                'success': True,
                'lines': len(lines),
                'split_count': len(multi_results),
                'splits': [
                    {
                        'level': result[2]['level'],
                        'description': result[2]['description'],
                        'split_type': result[2]['split_type'],
                        'prefix_length': len(result[0]),
                        'suffix_length': len(result[1]),
                        'prefix_ratio': len(result[0]) / (len(result[0]) + len(result[1])) * 100,
                        'suffix_ratio': len(result[1]) / (len(result[0]) + len(result[1])) * 100,
                        'prefix_preview': result[0][:200] + "..." if len(result[0]) > 200 else result[0],
                        'suffix_preview': result[1][:200] + "..." if len(result[1]) > 200 else result[1]
                    }
                    for result in multi_results
                ]
            }
        else:
            return {
                'file': file_path,
                'success': False,
                'reason': 'Multi-level splitter failed',
                'lines': len(lines)
            }
            
    except Exception as e:
        return {
            'file': file_path,
            'success': False,
            'reason': f'Error: {str(e)}',
            'lines': 0
        }

def analyze_multi_level_results(results: List[Dict]) -> Dict:
    """分析多层分割结果"""
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if not successful:
        return {
            'total_files': len(results),
            'successful_splits': 0,
            'failed_splits': len(failed),
            'success_rate': 0.0,
            'avg_split_count': 0.0,
            'level_distribution': {}
        }
    
    # 统计分割层级分布
    level_distribution = {}
    total_splits = 0
    
    for result in successful:
        for split in result['splits']:
            level = split['level']
            if level not in level_distribution:
                level_distribution[level] = 0
            level_distribution[level] += 1
            total_splits += 1
    
    avg_split_count = sum(r['split_count'] for r in successful) / len(successful)
    
    return {
        'total_files': len(results),
        'successful_splits': len(successful),
        'failed_splits': len(failed),
        'success_rate': len(successful) / len(results) * 100,
        'avg_split_count': avg_split_count,
        'total_split_count': total_splits,
        'level_distribution': level_distribution,
        'failed_reasons': {reason: len([r for r in failed if r['reason'] == reason]) 
                          for reason in set(r['reason'] for r in failed)}
    }

def main():
    """主测试函数"""
    print("=== 多层分割功能测试 ===")
    
    # 测试项目中的Java文件
    test_files = [
        'data_generation/direct_data_builder.py',
        'training/finetune.py',
        'data_generation/parsers/python_ast_parser.py'
    ]
    
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            result = test_multi_level_splitting(file_path)
            results.append(result)
        else:
            print(f"文件不存在: {file_path}")
    
    # 分析结果
    analysis = analyze_multi_level_results(results)
    
    print(f"\n=== 多层分割结果分析 ===")
    print(f"总文件数: {analysis['total_files']}")
    print(f"成功分割: {analysis['successful_splits']}")
    print(f"分割失败: {analysis['failed_splits']}")
    print(f"成功率: {analysis['success_rate']:.1f}%")
    print(f"平均分割数: {analysis['avg_split_count']:.1f}")
    print(f"总分割数: {analysis['total_split_count']}")
    
    print(f"\n分割层级分布:")
    for level, count in analysis['level_distribution'].items():
        print(f"  {level}: {count} 个分割点")
    
    if analysis['failed_reasons']:
        print(f"\n失败原因统计:")
        for reason, count in analysis['failed_reasons'].items():
            print(f"  {reason}: {count} 个文件")
    
    # 显示成功分割的详细信息
    print(f"\n=== 成功分割的详细信息 ===")
    for result in results:
        if result['success']:
            print(f"\n文件: {os.path.basename(result['file'])}")
            print(f"  行数: {result['lines']}")
            print(f"  分割数: {result['split_count']}")
            
            for i, split in enumerate(result['splits'], 1):
                print(f"  分割 {i} ({split['level']}):")
                print(f"    描述: {split['description']}")
                print(f"    类型: {split['split_type']}")
                print(f"    前缀比例: {split['prefix_ratio']:.1f}%")
                print(f"    后缀比例: {split['suffix_ratio']:.1f}%")
                print(f"    前缀预览: {split['prefix_preview']}")
                print(f"    后缀预览: {split['suffix_preview']}")
    
    # 保存详细结果到文件
    output_file = 'multi_level_splitting_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis': analysis,
            'detailed_results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
