#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_builder.py
----------------------------------------------------
显性架构实验数据构建脚本

功能：
1. 遍历源代码项目，生成显性/非显性架构副本
2. 构造函数补全任务样本
3. 计算函数间耦合度指标
4. 输出训练/验证/测试集

依赖：
    pip install astor tqdm networkx scikit-learn matplotlib pandas scipy
----------------------------------------------------
"""

import os
import ast
import json
import random
import shutil
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from pathlib import Path
from sklearn.model_selection import train_test_split
from scipy.stats import ttest_ind


# ========= 基础工具 ==========
def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def list_source_files(base_dir, supported_extensions=None):
    """递归列出目录下的所有源代码文件"""
    if supported_extensions is None:
        supported_extensions = [".py", ".java", ".js", ".ts", ".cpp", ".c", ".cs", ".go", ".rs"]
    
    source_files = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if any(f.endswith(ext) for ext in supported_extensions):
                source_files.append(os.path.join(root, f))
    return source_files


# ========= 1️⃣ 显性 / 非显性 副本生成 ==========
def make_copies(src_dir, out_dir):
    """
    生成显性和非显性架构副本
    
    Args:
        src_dir: 源代码目录
        out_dir: 输出目录
        
    Returns:
        tuple: (explicit_dir, implicit_dir) 路径
    """
    explicit_dir = Path(out_dir) / "explicit_view"
    implicit_dir = Path(out_dir) / "non_explicit_view"
    ensure_dir(explicit_dir)
    ensure_dir(implicit_dir)

    print(f"📁 处理源代码目录: {src_dir}")
    source_files = list_source_files(src_dir)
    print(f"📄 发现 {len(source_files)} 个源代码文件")

    for f in tqdm(source_files, desc="生成架构副本"):
        rel_path = os.path.relpath(f, src_dir)
        
        # 显性架构副本：保持原有目录结构
        explicit_dst = explicit_dir / rel_path
        ensure_dir(explicit_dst.parent)
        shutil.copy(f, explicit_dst)
        
        # 添加路径注释以增强位置信号
        try:
            with open(explicit_dst, "r", encoding="utf-8") as src_file:
                content = src_file.read()
            path_comment = f"# FILE_PATH: {rel_path}\n"
            with open(explicit_dst, "w", encoding="utf-8") as dst_file:
                dst_file.write(path_comment + content)
        except Exception as e:
            print(f"⚠️ 处理文件失败: {explicit_dst} - {e}")
        
        # 非显性架构副本：打乱结构，随机命名
        file_hash = abs(hash(rel_path)) % 999999
        file_ext = os.path.splitext(f)[1]  # 保持原文件扩展名
        implicit_dst = implicit_dir / f"file_{file_hash:06d}{file_ext}"
        shutil.copy(f, implicit_dst)

    print(f"✅ 已生成显性/非显性副本")
    print(f"   显性架构: {explicit_dir}")
    print(f"   非显性架构: {implicit_dir}")
    
    return str(explicit_dir), str(implicit_dir)


# ========= 2️⃣ 函数补全任务样本生成 ==========
def make_completion_samples(project_dir, label):
    """
    生成函数补全任务样本
    
    Args:
        project_dir: 项目目录
        label: 样本标签 ('explicit' 或 'non_explicit')
        
    Returns:
        list: 样本列表
    """
    samples = []
    source_files = list_source_files(project_dir)
    
    print(f"🔧 生成补全样本 [{label}] - {len(source_files)} 个文件")
    
    for f in tqdm(source_files, desc=f"处理 {label} 样本"):
        try:
            with open(f, "r", encoding="utf-8") as src:
                content = src.read()
            
            # 解析AST，提取函数定义
            try:
                functions = extract_functions_from_code(content, f)
            except Exception as e:
                print(f"⚠️ 解析错误，跳过文件: {f} - {e}")
                continue
            
            # 为每个函数生成补全样本
            for func_info in functions:
                if len(func_info['body'].strip()) < 10:  # 跳过太短的函数
                    continue
                    
                # 创建掩盖版本
                masked_content = create_masked_function(content, func_info)
                
                sample = {
                    "file": f,
                    "input": masked_content,
                    "target": func_info['body'],
                    "function_name": func_info['name'],
                    "view": label,
                    "line_start": func_info['line_start'],
                    "line_end": func_info['line_end']
                }
                samples.append(sample)
                
        except Exception as e:
            print(f"⚠️ 处理文件失败: {f} - {e}")
            continue
    
    print(f"✅ 生成 {len(samples)} 个补全样本 [{label}]")
    return samples


def extract_functions_from_code(content, file_path):
    """从代码中提取函数信息（支持多语言）"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.py':
        return extract_python_functions(content)
    elif file_ext == '.java':
        return extract_java_functions(content)
    elif file_ext in ['.js', '.ts']:
        return extract_javascript_functions(content)
    elif file_ext in ['.cpp', '.c']:
        return extract_cpp_functions(content)
    elif file_ext == '.cs':
        return extract_csharp_functions(content)
    else:
        # 对于其他语言，使用简单的正则表达式
        return extract_functions_with_regex(content, file_ext)


def extract_python_functions(content):
    """提取Python函数"""
    functions = []
    try:
        tree = ast.parse(content)
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                
                func_lines = lines[start_line:end_line]
                func_body = '\n'.join(func_lines)
                
                body_start = func_body.find(':') + 1
                if body_start > 0:
                    body_content = func_body[body_start:].strip()
                    if body_content:
                        functions.append({
                            'name': node.name,
                            'body': body_content,
                            'line_start': node.lineno,
                            'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                        })
    except Exception:
        pass
    
    return functions


def extract_java_functions(content):
    """提取Java方法"""
    import re
    functions = []
    lines = content.split('\n')
    
    # Java方法模式：修饰符 + 返回类型 + 方法名 + 参数 + {
    method_pattern = r'(\s*(?:public|private|protected|static|final|abstract|synchronized)\s+)*(\w+(?:<[^>]*>)?)\s+(\w+)\s*\([^)]*\)\s*\{'
    
    for i, line in enumerate(lines):
        match = re.search(method_pattern, line)
        if match:
            method_name = match.group(3)
            
            # 找到方法体的结束位置
            brace_count = 0
            start_line = i
            end_line = i
            
            for j in range(i, len(lines)):
                line_content = lines[j]
                brace_count += line_content.count('{')
                brace_count -= line_content.count('}')
                
                if brace_count == 0 and j > i:
                    end_line = j
                    break
            
            # 提取方法体
            method_lines = lines[start_line:end_line + 1]
            method_body = '\n'.join(method_lines)
            
            # 找到第一个{后的内容
            body_start = method_body.find('{') + 1
            if body_start > 0:
                body_content = method_body[body_start:].strip()
                if body_content and len(body_content) > 10:
                    functions.append({
                        'name': method_name,
                        'body': body_content,
                        'line_start': start_line + 1,
                        'line_end': end_line + 1
                    })
    
    return functions


def extract_javascript_functions(content):
    """提取JavaScript/TypeScript函数"""
    import re
    functions = []
    lines = content.split('\n')
    
    # JavaScript函数模式
    patterns = [
        r'function\s+(\w+)\s*\([^)]*\)\s*\{',  # function name() {}
        r'(\w+)\s*:\s*function\s*\([^)]*\)\s*\{',  # name: function() {}
        r'(\w+)\s*\([^)]*\)\s*=>\s*\{',  # name() => {}
        r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{',  # const name = () => {}
    ]
    
    for pattern in patterns:
        for i, line in enumerate(lines):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                
                # 找到函数体的结束位置
                brace_count = 0
                start_line = i
                end_line = i
                
                for j in range(i, len(lines)):
                    line_content = lines[j]
                    brace_count += line_content.count('{')
                    brace_count -= line_content.count('}')
                    
                    if brace_count == 0 and j > i:
                        end_line = j
                        break
                
                # 提取函数体
                func_lines = lines[start_line:end_line + 1]
                func_body = '\n'.join(func_lines)
                
                body_start = func_body.find('{') + 1
                if body_start > 0:
                    body_content = func_body[body_start:].strip()
                    if body_content and len(body_content) > 10:
                        functions.append({
                            'name': func_name,
                            'body': body_content,
                            'line_start': start_line + 1,
                            'line_end': end_line + 1
                        })
    
    return functions


def extract_cpp_functions(content):
    """提取C++函数"""
    import re
    functions = []
    lines = content.split('\n')
    
    # C++函数模式
    function_pattern = r'(\w+(?:\s*<[^>]*>)?)\s+(\w+)\s*\([^)]*\)\s*\{'
    
    for i, line in enumerate(lines):
        match = re.search(function_pattern, line)
        if match:
            func_name = match.group(2)
            
            # 找到函数体的结束位置
            brace_count = 0
            start_line = i
            end_line = i
            
            for j in range(i, len(lines)):
                line_content = lines[j]
                brace_count += line_content.count('{')
                brace_count -= line_content.count('}')
                
                if brace_count == 0 and j > i:
                    end_line = j
                    break
            
            # 提取函数体
            func_lines = lines[start_line:end_line + 1]
            func_body = '\n'.join(func_lines)
            
            body_start = func_body.find('{') + 1
            if body_start > 0:
                body_content = func_body[body_start:].strip()
                if body_content and len(body_content) > 10:
                    functions.append({
                        'name': func_name,
                        'body': body_content,
                        'line_start': start_line + 1,
                        'line_end': end_line + 1
                    })
    
    return functions


def extract_csharp_functions(content):
    """提取C#方法"""
    import re
    functions = []
    lines = content.split('\n')
    
    # C#方法模式
    method_pattern = r'(\s*(?:public|private|protected|internal|static|virtual|override|abstract|sealed)\s+)*(\w+(?:<[^>]*>)?)\s+(\w+)\s*\([^)]*\)\s*\{'
    
    for i, line in enumerate(lines):
        match = re.search(method_pattern, line)
        if match:
            method_name = match.group(3)
            
            # 找到方法体的结束位置
            brace_count = 0
            start_line = i
            end_line = i
            
            for j in range(i, len(lines)):
                line_content = lines[j]
                brace_count += line_content.count('{')
                brace_count -= line_content.count('}')
                
                if brace_count == 0 and j > i:
                    end_line = j
                    break
            
            # 提取方法体
            method_lines = lines[start_line:end_line + 1]
            method_body = '\n'.join(method_lines)
            
            body_start = method_body.find('{') + 1
            if body_start > 0:
                body_content = method_body[body_start:].strip()
                if body_content and len(body_content) > 10:
                    functions.append({
                        'name': method_name,
                        'body': body_content,
                        'line_start': start_line + 1,
                        'line_end': end_line + 1
                    })
    
    return functions


def extract_functions_with_regex(content, file_ext):
    """使用正则表达式提取函数（通用方法）"""
    import re
    functions = []
    lines = content.split('\n')
    
    # 通用函数模式
    patterns = [
        r'(\w+)\s*\([^)]*\)\s*\{',  # name() {
        r'function\s+(\w+)\s*\([^)]*\)\s*\{',  # function name() {
    ]
    
    for pattern in patterns:
        for i, line in enumerate(lines):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                
                # 找到函数体的结束位置
                brace_count = 0
                start_line = i
                end_line = i
                
                for j in range(i, len(lines)):
                    line_content = lines[j]
                    brace_count += line_content.count('{')
                    brace_count -= line_content.count('}')
                    
                    if brace_count == 0 and j > i:
                        end_line = j
                        break
                
                # 提取函数体
                func_lines = lines[start_line:end_line + 1]
                func_body = '\n'.join(func_lines)
                
                body_start = func_body.find('{') + 1
                if body_start > 0:
                    body_content = func_body[body_start:].strip()
                    if body_content and len(body_content) > 10:
                        functions.append({
                            'name': func_name,
                            'body': body_content,
                            'line_start': start_line + 1,
                            'line_end': end_line + 1
                        })
    
    return functions


def create_masked_function(content, func_info):
    """创建掩盖函数体的版本"""
    lines = content.split('\n')
    start_line = func_info['line_start'] - 1
    end_line = func_info['line_end'] - 1
    
    # 找到函数定义行
    func_def_line = start_line
    for i in range(start_line, min(end_line + 1, len(lines))):
        if 'def ' in lines[i] and func_info['name'] in lines[i]:
            func_def_line = i
            break
    
    # 创建掩盖版本
    masked_lines = lines[:func_def_line + 1]  # 保留函数定义行
    masked_lines.append("    # [MASKED_FUNCTION_BODY]")
    masked_lines.extend(lines[end_line + 1:])  # 保留函数后的内容
    
    return '\n'.join(masked_lines)


# ========= 3️⃣ 函数调用与导入图分析 ==========
class FunctionCallAnalyzer(ast.NodeVisitor):
    """AST访问器，用于分析函数调用关系"""
    
    def __init__(self, filename):
        self.filename = filename
        self.calls = []  # (caller, callee)
        self.current_func = None

    def visit_FunctionDef(self, node):
        prev = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = prev

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            name = f"{ast.unparse(node.func)}"
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        else:
            name = "unknown"
        
        if self.current_func:
            self.calls.append((self.current_func, name))
        self.generic_visit(node)


def parse_imports(filepath):
    """解析文件的导入语句（支持多语言）"""
    file_ext = os.path.splitext(filepath)[1].lower()
    
    if file_ext == '.py':
        return parse_python_imports(filepath)
    elif file_ext == '.java':
        return parse_java_imports(filepath)
    elif file_ext in ['.js', '.ts']:
        return parse_javascript_imports(filepath)
    elif file_ext in ['.cpp', '.c']:
        return parse_cpp_imports(filepath)
    elif file_ext == '.cs':
        return parse_csharp_imports(filepath)
    else:
        return parse_imports_with_regex(filepath)


def parse_python_imports(filepath):
    """解析Python导入语句"""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return imports
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    
    return imports


def parse_java_imports(filepath):
    """解析Java导入语句"""
    import re
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Java import语句模式
        import_pattern = r'import\s+(?:static\s+)?([^;]+);'
        matches = re.findall(import_pattern, content)
        
        for match in matches:
            imports.append(match.strip())
    except Exception:
        pass
    
    return imports


def parse_javascript_imports(filepath):
    """解析JavaScript/TypeScript导入语句"""
    import re
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # JavaScript/TypeScript导入模式
        patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',  # import ... from '...'
            r'import\s+[\'"]([^\'"]+)[\'"]',  # import '...'
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',  # require('...')
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
    except Exception:
        pass
    
    return imports


def parse_cpp_imports(filepath):
    """解析C++导入语句"""
    import re
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # C++ include语句模式
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        matches = re.findall(include_pattern, content)
        
        for match in matches:
            imports.append(match.strip())
    except Exception:
        pass
    
    return imports


def parse_csharp_imports(filepath):
    """解析C#导入语句"""
    import re
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # C# using语句模式
        using_pattern = r'using\s+([^;]+);'
        matches = re.findall(using_pattern, content)
        
        for match in matches:
            imports.append(match.strip())
    except Exception:
        pass
    
    return imports


def parse_imports_with_regex(filepath):
    """使用正则表达式解析导入语句（通用方法）"""
    import re
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 通用导入模式
        patterns = [
            r'import\s+([^;]+);',  # import ...;
            r'#include\s*[<"]([^>"]+)[>"]',  # #include <...>
            r'using\s+([^;]+);',  # using ...;
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
    except Exception:
        pass
    
    return imports


def analyze_calls_with_regex(content, filepath):
    """使用正则表达式分析函数调用（通用方法）"""
    import re
    calls = []
    lines = content.split('\n')
    
    # 首先提取所有函数定义
    functions = extract_functions_from_code(content, filepath)
    function_names = [func['name'] for func in functions]
    
    # 分析每个函数中的调用
    for func in functions:
        func_name = func['name']
        start_line = func['line_start'] - 1
        end_line = func['line_end'] - 1
        
        # 提取函数体内容
        func_lines = lines[start_line:end_line]
        func_content = '\n'.join(func_lines)
        
        # 查找函数调用
        # 匹配模式：函数名(参数)
        call_pattern = r'(\w+)\s*\('
        matches = re.findall(call_pattern, func_content)
        
        for match in matches:
            # 检查是否是已知的函数
            if match in function_names and match != func_name:
                calls.append((func_name, match))
    
    return calls


def compute_coupling(project_dir):
    """
    计算项目的耦合度指标
    
    Args:
        project_dir: 项目目录
        
    Returns:
        dict: 每个文件的耦合度指标
    """
    files = list_source_files(project_dir)
    import_graph = nx.DiGraph()
    call_graph = nx.DiGraph()
    
    print(f"🔍 计算耦合度指标 - {len(files)} 个文件")
    
    # 构建导入图
    for f in tqdm(files, desc="分析导入关系"):
        imports = parse_imports(f)
        for imp in imports:
            import_graph.add_edge(f, imp)
    
    # 构建调用图
    for f in tqdm(files, desc="分析调用关系"):
        try:
            with open(f, "r", encoding="utf-8") as src:
                content = src.read()
            
            # 根据文件类型选择分析方法
            file_ext = os.path.splitext(f)[1].lower()
            if file_ext == '.py':
                tree = ast.parse(content)
                analyzer = FunctionCallAnalyzer(f)
                analyzer.visit(tree)
                for caller, callee in analyzer.calls:
                    call_graph.add_edge(f"{f}:{caller}", callee)
            else:
                # 对于其他语言，使用正则表达式分析
                calls = analyze_calls_with_regex(content, f)
                for caller, callee in calls:
                    call_graph.add_edge(f"{f}:{caller}", callee)
        except Exception:
            continue
    
    # 计算每个文件的耦合度指标
    results = {}
    for f in files:
        import_deg = import_graph.out_degree(f)
        call_deg = sum(1 for n in call_graph.nodes if n.startswith(f + ":"))
        coupling_score = round(import_deg * 0.4 + call_deg * 0.6, 3)
        
        results[f] = {
            "import_coupling": import_deg,
            "call_coupling": call_deg,
            "coupling_score": coupling_score
        }
    
    return results


# ========= 4️⃣ 耦合度统计分析与可视化 ==========
def analyze_coupling_diff(explicit_coupling, implicit_coupling, out_dir):
    """
    分析显性和非显性架构的耦合度差异
    
    Args:
        explicit_coupling: 显性架构耦合度数据
        implicit_coupling: 非显性架构耦合度数据
        out_dir: 输出目录
    """
    # 转换为DataFrame
    df_exp = pd.DataFrame([
        {"file": f, **v, "view": "explicit"} for f, v in explicit_coupling.items()
    ])
    df_imp = pd.DataFrame([
        {"file": f, **v, "view": "non_explicit"} for f, v in implicit_coupling.items()
    ])
    df = pd.concat([df_exp, df_imp], ignore_index=True)
    
    # 保存详细报告
    report_csv = Path(out_dir) / "coupling_report.csv"
    ensure_dir(out_dir)
    df.to_csv(report_csv, index=False, encoding="utf-8-sig")
    print(f"📊 耦合度报告已保存至: {report_csv}")
    
    # 计算平均值
    metrics = ["import_coupling", "call_coupling", "coupling_score"]
    summary = df.groupby("view")[metrics].mean()
    print("\n=== 平均耦合度对比 ===")
    print(summary)
    
    # 统计检验
    print("\n=== 统计检验结果 ===")
    signif_dict = {}
    for m in metrics:
        exp_values = df_exp[m].values
        imp_values = df_imp[m].values
        t_stat, p_val = ttest_ind(exp_values, imp_values, equal_var=False)
        signif_dict[m] = p_val
        delta = summary.loc['non_explicit', m] - summary.loc['explicit', m]
        print(f"{m}: Δ = {delta:.3f}, p-value = {p_val:.4f}")
    
    # 绘制对比图
    plt.figure(figsize=(12, 8))
    x = np.arange(len(metrics))
    bar_width = 0.35
    
    plt.bar(x - bar_width/2, summary.loc["explicit"], bar_width, 
            label="显性架构", color='skyblue', alpha=0.8)
    plt.bar(x + bar_width/2, summary.loc["non_explicit"], bar_width, 
            label="非显性架构", color='lightcoral', alpha=0.8)
    
    # 标注统计显著性
    for idx, m in enumerate(metrics):
        delta = summary.loc["non_explicit", m] - summary.loc["explicit", m]
        p_val = signif_dict[m]
        if p_val < 0.001:
            star = "***"
        elif p_val < 0.01:
            star = "**"
        elif p_val < 0.05:
            star = "*"
        else:
            star = "ns"
        
        y_pos = max(summary.loc["explicit", m], summary.loc["non_explicit", m]) + 0.5
        plt.text(idx, y_pos, f"Δ={delta:.2f}\n{star}", 
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.xticks(x, metrics)
    plt.ylabel("平均耦合度")
    plt.title("显性架构 vs 非显性架构 - 耦合度对比")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    
    # 保存图表
    chart_path = Path(out_dir) / "coupling_comparison.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"📈 对比图表已保存至: {chart_path}")
    plt.show()


# ========= 5️⃣ 样本处理与划分 ==========
def attach_coupling(samples, coupling_dict):
    """为样本附加耦合度信息"""
    for s in samples:
        f = s["file"]
        if f in coupling_dict:
            s["coupling"] = coupling_dict[f]
        else:
            s["coupling"] = {"import_coupling": 0, "call_coupling": 0, "coupling_score": 0}
    return samples


def save_and_split(samples, out_prefix):
    """保存样本并划分训练/验证集"""
    ensure_dir(os.path.dirname(out_prefix))
    
    # 保存完整样本
    with open(out_prefix + ".json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    # 划分训练/验证集
    train, val = train_test_split(samples, test_size=0.2, random_state=42)
    
    with open(out_prefix + "_train.json", "w", encoding="utf-8") as f:
        json.dump(train, f, indent=2, ensure_ascii=False)
    with open(out_prefix + "_val.json", "w", encoding="utf-8") as f:
        json.dump(val, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 样本划分完成: 训练集 {len(train)} / 验证集 {len(val)}")


# ========= 主流程 ==========
def main(src_dir, out_dir):
    """
    主数据构建流程
    
    Args:
        src_dir: 源代码目录
        out_dir: 输出目录
    """
    print("🚀 开始显性架构实验数据构建")
    print(f"📂 源代码目录: {src_dir}")
    print(f"📁 输出目录: {out_dir}")
    
    # 1. 生成显性/非显性架构副本
    explicit_dir, implicit_dir = make_copies(src_dir, out_dir)
    
    # 2. 生成补全任务样本
    exp_samples = make_completion_samples(explicit_dir, "explicit")
    imp_samples = make_completion_samples(implicit_dir, "non_explicit")
    
    # 3. 计算耦合度指标
    exp_coupling = compute_coupling(explicit_dir)
    imp_coupling = compute_coupling(implicit_dir)
    
    # 4. 分析耦合度差异
    analyze_coupling_diff(exp_coupling, imp_coupling, out_dir)
    
    # 5. 附加耦合度信息并保存
    exp_samples = attach_coupling(exp_samples, exp_coupling)
    imp_samples = attach_coupling(imp_samples, imp_coupling)
    
    save_and_split(exp_samples, f"{out_dir}/explicit_samples")
    save_and_split(imp_samples, f"{out_dir}/non_explicit_samples")
    
    print("🎯 数据构建流程完成！")
    print(f"📊 显性架构样本: {len(exp_samples)} 个")
    print(f"📊 非显性架构样本: {len(imp_samples)} 个")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="显性架构实验数据构建脚本")
    parser.add_argument("--src", required=True, help="源代码项目目录")
    parser.add_argument("--out", default="./dataset_out", help="输出目录")
    args = parser.parse_args()
    
    main(args.src, args.out)
