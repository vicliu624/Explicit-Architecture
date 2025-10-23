#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_current_status.py
测试当前 SmartJavaSplitterV2 的状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import SmartJavaSplitterV2

def main():
    print('当前 SmartJavaSplitterV2 状态:')
    splitter = SmartJavaSplitterV2()
    print(f'use_tree_sitter: {splitter.use_tree_sitter}')
    print(f'parser 可用: {splitter.parser is not None}')
    
    # 测试一个简单的 Java 代码
    test_code = '''public class Test {
    public void method() {
        System.out.println("Hello");
    }
}'''
    
    result = splitter.split_file(test_code, mode='best')
    if result:
        print(f'分割成功: {result[0].candidate.node_type} (评分: {result[0].candidate.score:.4f})')
        print(f'使用模式: {result[0].candidate.description}')
    else:
        print('分割失败')

if __name__ == "__main__":
    main()
