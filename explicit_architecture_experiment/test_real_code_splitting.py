#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_real_code_splitting.py
----------------------------------------------------
测试真实项目代码的分割效果

功能：
1. 使用项目中的真实代码文件测试分割器
2. 分析分割质量和效果
3. 生成分割报告
----------------------------------------------------
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import get_code_splitter, get_supported_languages

def test_file_splitting(file_path: str, language: str) -> Dict:
    """测试单个文件的分割效果"""
    print(f"\n=== 测试文件: {file_path} ===")
    
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
        
        # 获取对应的分割器
        splitter = get_code_splitter(language)
        result = splitter.split_code(lines)
        
        if result:
            prefix, suffix = result
            total_length = len(prefix) + len(suffix)
            prefix_ratio = len(prefix) / total_length * 100
            suffix_ratio = len(suffix) / total_length * 100
            
            return {
                'file': file_path,
                'success': True,
                'lines': len(lines),
                'prefix_length': len(prefix),
                'suffix_length': len(suffix),
                'prefix_ratio': prefix_ratio,
                'suffix_ratio': suffix_ratio,
                'prefix_preview': prefix[:200] + "..." if len(prefix) > 200 else prefix,
                'suffix_preview': suffix[:200] + "..." if len(suffix) > 200 else suffix
            }
        else:
            return {
                'file': file_path,
                'success': False,
                'reason': 'Splitter failed to split',
                'lines': len(lines)
            }
            
    except Exception as e:
        return {
            'file': file_path,
            'success': False,
            'reason': f'Error: {str(e)}',
            'lines': 0
        }

def analyze_splitting_results(results: List[Dict]) -> Dict:
    """分析分割结果"""
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if not successful:
        return {
            'total_files': len(results),
            'successful_splits': 0,
            'failed_splits': len(failed),
            'success_rate': 0.0,
            'average_prefix_ratio': 0.0,
            'average_suffix_ratio': 0.0
        }
    
    avg_prefix_ratio = sum(r['prefix_ratio'] for r in successful) / len(successful)
    avg_suffix_ratio = sum(r['suffix_ratio'] for r in successful) / len(successful)
    
    return {
        'total_files': len(results),
        'successful_splits': len(successful),
        'failed_splits': len(failed),
        'success_rate': len(successful) / len(results) * 100,
        'average_prefix_ratio': avg_prefix_ratio,
        'average_suffix_ratio': avg_suffix_ratio,
        'failed_reasons': {reason: len([r for r in failed if r['reason'] == reason]) 
                          for reason in set(r['reason'] for r in failed)}
    }

def main():
    """主测试函数"""
    print("=== 真实代码分割测试 ===")
    print(f"支持的语言: {', '.join(get_supported_languages())}")
    
    # 测试项目中的 Python 文件
    test_files = [
        'data_generation/direct_data_builder.py',
        'training/finetune.py',
        'data_generation/parsers/python_ast_parser.py',
        'evaluation/eval_pipeline.py',
        'analysis/generate_report.py'
    ]
    
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            result = test_file_splitting(file_path, 'py')
            results.append(result)
        else:
            print(f"文件不存在: {file_path}")
    
    # 分析结果
    analysis = analyze_splitting_results(results)
    
    print(f"\n=== 分割结果分析 ===")
    print(f"总文件数: {analysis['total_files']}")
    print(f"成功分割: {analysis['successful_splits']}")
    print(f"分割失败: {analysis['failed_splits']}")
    print(f"成功率: {analysis['success_rate']:.1f}%")
    print(f"平均前缀比例: {analysis['average_prefix_ratio']:.1f}%")
    print(f"平均后缀比例: {analysis['average_suffix_ratio']:.1f}%")
    
    if analysis['failed_reasons']:
        print(f"\n失败原因统计:")
        for reason, count in analysis['failed_reasons'].items():
            print(f"  {reason}: {count} 个文件")
    
    # 显示成功分割的详细信息
    print(f"\n=== 成功分割的详细信息 ===")
    for result in results:
        if result['success']:
            print(f"\n文件: {result['file']}")
            print(f"  行数: {result['lines']}")
            print(f"  前缀长度: {result['prefix_length']} 字符 ({result['prefix_ratio']:.1f}%)")
            print(f"  后缀长度: {result['suffix_length']} 字符 ({result['suffix_ratio']:.1f}%)")
            print(f"  前缀预览: {result['prefix_preview']}")
            print(f"  后缀预览: {result['suffix_preview']}")
    
    # 保存详细结果到文件
    output_file = 'splitting_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis': analysis,
            'detailed_results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
