#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
java_parser.py
----------------------------------------------------
Java代码解析器

功能：
1. 解析Java import语句
2. 解析Java方法调用
3. 计算Java项目的耦合度指标

依赖：
    pip install javalang
----------------------------------------------------
"""

import re
import os
from typing import List, Dict, Tuple

def parse_java_imports(filepath: str) -> List[str]:
    """解析Java import语句"""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配 import 语句
        import_pattern = r'import\s+(?:static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'
        matches = re.findall(import_pattern, content)
        imports.extend(matches)
        
        # 匹配 package 语句
        package_pattern = r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'
        package_matches = re.findall(package_pattern, content)
        imports.extend(package_matches)
        
    except Exception as e:
        print(f"⚠️ 解析import失败: {filepath} - {e}")
    
    return imports

def parse_java_method_calls(filepath: str) -> List[Tuple[str, str]]:
    """解析Java方法调用"""
    calls = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配方法调用: object.method() 或 method()
        method_call_pattern = r'(\w+)\s*\.\s*(\w+)\s*\('
        matches = re.findall(method_call_pattern, content)
        for obj, method in matches:
            calls.append((f"{obj}.{method}", method))
        
        # 匹配直接方法调用: method()
        direct_call_pattern = r'(?:^|\s|;|{|})\s*(\w+)\s*\('
        direct_matches = re.findall(direct_call_pattern, content)
        for method in direct_matches:
            if method not in ['if', 'for', 'while', 'switch', 'catch', 'try', 'new', 'return']:
                calls.append((method, method))
        
        # 匹配构造函数调用: new ClassName()
        constructor_pattern = r'new\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*\('
        constructor_matches = re.findall(constructor_pattern, content)
        for constructor in constructor_matches:
            calls.append((f"new {constructor}", constructor))
        
    except Exception as e:
        print(f"⚠️ 解析方法调用失败: {filepath} - {e}")
    
    return calls

def extract_java_methods(filepath: str) -> List[str]:
    """提取Java方法定义"""
    methods = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配方法定义
        method_pattern = r'(?:public|private|protected|static|\s)*\s*(?:final|abstract|\s)*\s*(?:void|\w+)\s+(\w+)\s*\('
        matches = re.findall(method_pattern, content)
        methods.extend(matches)
        
        # 匹配构造函数
        constructor_pattern = r'(?:public|private|protected)\s+([A-Z][a-zA-Z0-9_]*)\s*\('
        constructor_matches = re.findall(constructor_pattern, content)
        methods.extend(constructor_matches)
        
    except Exception as e:
        print(f"⚠️ 提取方法定义失败: {filepath} - {e}")
    
    return methods

def compute_java_coupling(project_dir: str) -> Dict[str, Dict]:
    """计算Java项目的耦合度指标"""
    import networkx as nx
    
    # 获取所有Java文件
    java_files = []
    for root, _, files in os.walk(project_dir):
        for f in files:
            if f.endswith('.java'):
                java_files.append(os.path.join(root, f))
    
    print(f"📄 发现 {len(java_files)} 个Java文件")
    
    # 构建图
    import_graph = nx.DiGraph()
    call_graph = nx.DiGraph()
    
    # 建立文件索引
    file_methods = {}
    for f in java_files:
        methods = extract_java_methods(f)
        file_methods[f] = methods
        for method in methods:
            call_graph.add_node(f"{f}:{method}")
    
    # 分析每个文件
    for f in java_files:
        # 解析导入
        imports = parse_java_imports(f)
        for imp in imports:
            import_graph.add_edge(f, imp)
        
        # 解析方法调用
        calls = parse_java_method_calls(f)
        for caller_method, callee in calls:
            # 找到调用者方法
            for method in file_methods.get(f, []):
                if caller_method.startswith(method) or method in caller_method:
                    caller_node = f"{f}:{method}"
                    # 添加调用边
                    call_graph.add_edge(caller_node, callee)
    
    # 计算耦合度指标
    results = {}
    for f in java_files:
        # 导入耦合度
        import_deg = import_graph.out_degree(f)
        if hasattr(import_deg, '__iter__') and not isinstance(import_deg, (int, float)):
            import_deg = len(list(import_deg))
        else:
            import_deg = int(import_deg)
        
        # 调用耦合度
        call_deg = sum(1 for n in call_graph.nodes if n.startswith(f + ":"))
        
        # 综合耦合度
        coupling_score = round(import_deg * 0.4 + call_deg * 0.6, 3)
        
        results[f] = {
            "import_coupling": import_deg,
            "call_coupling": call_deg,
            "coupling_score": coupling_score
        }
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Java项目耦合度分析")
    parser.add_argument("--project_dir", required=True, help="Java项目目录")
    parser.add_argument("--output", default="java_coupling_report.csv", help="输出文件")
    
    args = parser.parse_args()
    
    coupling = compute_java_coupling(args.project_dir)
    
    # 保存结果
    import pandas as pd
    df = pd.DataFrame([
        {"file": f, **v} for f, v in coupling.items()
    ])
    df.to_csv(args.output, index=False, encoding='utf-8-sig')
    
    print(f"✅ Java耦合度分析完成，结果保存至: {args.output}")
    print(f"📊 平均耦合度: {df['coupling_score'].mean():.3f}")
