#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
direct_data_builder.py
----------------------------------------------------
直接数据构建脚本 - 用于处理单个项目

功能：
1. 直接处理单个项目（MVC或显性架构）
2. 生成函数补全任务样本
3. 计算函数间耦合度指标
4. 输出训练/验证/测试集

依赖：
    pip install astor tqdm networkx scikit-learn matplotlib pandas scipy
----------------------------------------------------
"""
import re
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
import argparse
try:
    # 尝试相对导入（当作为模块使用时）
    from .code_splitters import get_code_splitter, get_supported_languages, SmartJavaSplitterV2
    from .parsers import get_parser as get_ast_parser
except ImportError:
    # 绝对导入（当作为脚本直接运行时）
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from code_splitters import get_code_splitter, get_supported_languages, SmartJavaSplitterV2
    from parsers import get_parser as get_ast_parser

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

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

# ========= 1️⃣ 函数补全任务样本生成 ==========
def make_completion_samples(project_dir, view_type):
    """生成函数补全任务样本"""
    samples = []
    source_files = list_source_files(project_dir)
    
    print(f"发现 {len(source_files)} 个源代码文件")
    print(f"支持的语言: {', '.join(get_supported_languages())}")
    
    for f in tqdm(source_files, desc=f"生成补全样本 [{view_type}]"):
        try:
            with open(f, "r", encoding="utf-8") as src:
                lines = src.readlines()
            
            if len(lines) < 4:
                continue
            
            # 根据文件扩展名确定语言
            file_ext = os.path.splitext(f)[1].lower()
            language_map = {
                '.java': 'java',
                '.py': 'py',
                '.js': 'js',
                '.ts': 'ts',
                '.cpp': 'cpp',
                '.c': 'c',
                '.cs': 'cs',
                '.go': 'go',
                '.rs': 'rs'
            }
            
            language = language_map.get(file_ext)
            if not language:
                print(f"不支持的文件类型: {f}")
                continue
            
            # 使用对应的代码分割器
            try:
                # 对于Java文件，优先使用SmartJavaSplitterV2
                if language == 'java':
                    splitter = SmartJavaSplitterV2()
                    content = ''.join(lines)
                    result = splitter.split_file(content, mode='best')
                    
                    if result and len(result) > 0:
                        split_result = result[0]  # 取第一个（最佳）分割结果
                        prefix = split_result.prefix
                        suffix = split_result.suffix
                        
                        samples.append({
                            "file": f,
                            "prefix": prefix,
                            "suffix": suffix,
                            "view": view_type,
                            "project": os.path.basename(project_dir),
                            "language": language,
                            "split_line": split_result.split_line,
                            "split_score": split_result.candidate.score,
                            "split_type": split_result.candidate.node_type,
                            "split_description": split_result.candidate.description
                        })
                    else:
                        print(f"SmartJavaSplitterV2 无法分割文件: {f}")
                else:
                    # 其他语言使用原有分割器
                    splitter = get_code_splitter(language)
                    result = splitter.split_code(lines)
                    
                    if result:
                        prefix, suffix = result
                        samples.append({
                            "file": f,
                            "prefix": prefix,
                            "suffix": suffix,
                            "view": view_type,
                            "project": os.path.basename(project_dir),
                            "language": language
                        })
                    else:
                        print(f"无法分割文件: {f}")
                    
            except NotImplementedError:
                print(f"{language} 分割器尚未实现，跳过文件: {f}")
                continue
            except Exception as e:
                print(f"分割器错误: {f} - {e}")
                continue
                
        except Exception as e:
            print(f"处理文件失败: {f} - {e}")
            continue
    
    return samples

# ========= 2️⃣ 函数调用与导入图分析 ==========
class FunctionCallAnalyzer(ast.NodeVisitor):
    """函数调用分析器"""
    def __init__(self, filename):
        self.filename = filename
        self.calls = []
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
    """解析导入语句"""
    imports = []
    
    # 根据文件扩展名选择解析器
    if filepath.endswith('.java'):
        return parse_java_imports(filepath)
    elif filepath.endswith('.py'):
        return parse_python_imports(filepath)
    else:
        return imports

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
    """解析Java导入语句 - 使用AST-based解析器"""
    try:
        # 使用新的AST解析器
        parser = get_ast_parser('java')
        ast_info = parser.parse_file(filepath)
        
        # 从AST信息中提取导入
        imports = []
        
        # 添加package信息
        if ast_info.get('package'):
            imports.append(ast_info['package'])
        
        # 添加import信息
        imports.extend(ast_info.get('imports', []))
        
        return imports
        
    except Exception as e:
        print(f" AST解析失败，使用备用方法: {filepath} - {e}")
        # 备用方法：改进的正则表达式
        return _parse_java_imports_fallback(filepath)


def _parse_java_imports_fallback(filepath):
    """备用的Java导入解析方法"""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 改进的import模式
        import_patterns = [
            # 标准import
            r'import\s+(?:static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*)\s*;',
            # 静态import
            r'import\s+static\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;',
            # package声明
            r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
    except Exception as e:
        print(f" 备用解析方法也失败: {filepath} - {e}")
    
    return imports

def parse_java_method_calls(filepath):
    """解析Java方法调用 - 使用AST-based解析器"""
    try:
        # 使用新的AST解析器
        parser = get_ast_parser('java')
        ast_info = parser.parse_file(filepath)
        
        # 从AST信息中提取方法调用
        calls = []
        for call_info in ast_info.get('method_calls', []):
            if call_info['type'] == 'instance_call':
                calls.append((f"{call_info['object']}.{call_info['method']}", call_info['method']))
            elif call_info['type'] == 'direct_call':
                calls.append((call_info['method'], call_info['method']))
            elif call_info['type'] == 'constructor_call':
                calls.append((f"new {call_info['method']}", call_info['method']))
        
        return calls
        
    except Exception as e:
        print(f" AST解析失败，使用备用方法: {filepath} - {e}")
        # 备用方法：改进的正则表达式
        return _parse_java_method_calls_fallback(filepath)


def _parse_java_method_calls_fallback(filepath):
    """备用的Java方法调用解析方法"""
    calls = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 改进的方法调用模式
        method_call_patterns = [
            r'(\w+)\s*\.\s*(\w+)\s*\(',  # object.method()
            r'(\w+)\s*\.\s*(\w+)\s*\[',  # object.method[]
            r'(\w+)\s*\.\s*(\w+)\s*\.',  # object.method.
        ]
        
        for pattern in method_call_patterns:
            matches = re.findall(pattern, content)
            for obj, method in matches:
                calls.append((f"{obj}.{method}", method))
        
        # 直接方法调用（排除关键字）
        java_keywords = {'if', 'for', 'while', 'switch', 'catch', 'try', 'new', 'return', 'throw', 'assert'}
        direct_call_pattern = r'(?:^|\s|;|{|})\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        direct_matches = re.findall(direct_call_pattern, content)
        for method in direct_matches:
            if method not in java_keywords:
                calls.append((method, method))
        
        # 构造函数调用
        constructor_pattern = r'new\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*\('
        constructor_matches = re.findall(constructor_pattern, content)
        for constructor in constructor_matches:
            calls.append((f"new {constructor}", constructor))
        
    except Exception as e:
        print(f" 备用解析方法也失败: {filepath} - {e}")
    
    return calls

def extract_java_methods(filepath):
    """提取Java方法定义 - 使用AST-based解析器"""
    try:
        # 使用新的AST解析器
        parser = get_ast_parser('java')
        ast_info = parser.parse_file(filepath)
        
        # 从AST信息中提取方法定义
        methods = []
        
        # 提取普通方法
        for method_info in ast_info.get('methods', []):
            methods.append(method_info['name'])
        
        # 提取构造函数
        for constructor_info in ast_info.get('constructors', []):
            methods.append(constructor_info['name'])
        
        return methods
        
    except Exception as e:
        print(f" AST解析失败，使用备用方法: {filepath} - {e}")
        # 备用方法：改进的正则表达式
        return _extract_java_methods_fallback(filepath)


def _extract_java_methods_fallback(filepath):
    """备用的Java方法定义提取方法"""
    methods = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 改进的方法定义模式
        method_patterns = [
            # 标准方法定义
            r'(?:public|private|protected|package-private)?\s*(?:static|final|abstract|synchronized|native|strictfp|default)?\s*(?:<[^>]*>)?\s*(?:void|\w+(?:<[^>]*>)?(?:\s*\[\])*)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{;]+)?\s*[;{]',
            # 构造函数定义
            r'(?:public|private|protected|package-private)?\s*([A-Z][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:throws\s+[^{;]+)?\s*[;{]',
            # 接口方法定义
            r'(?:default|static)?\s*(?:<[^>]*>)?\s*(?:void|\w+(?:<[^>]*>)?(?:\s*\[\])*)\s+(\w+)\s*\([^)]*\)\s*;',
        ]
        
        for pattern in method_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            methods.extend(matches)
        
        # 去重
        methods = list(set(methods))
        
    except Exception as e:
        print(f" 备用提取方法也失败: {filepath} - {e}")
    
    return methods

def compute_coupling(project_dir):
    """计算耦合度指标 - 使用改进的AST-based解析"""
    files = list_source_files(project_dir)
    import_graph = nx.DiGraph()
    call_graph = nx.DiGraph()

    print(f"计算耦合度指标...")
    
    for f in tqdm(files, desc="分析文件"):
        try:
            # 解析导入
            imports = parse_imports(f)
            for imp in imports:
                import_graph.add_edge(f, imp)

            # 解析函数调用 - 使用改进的方法
            if f.endswith('.java'):
                _analyze_java_coupling(f, call_graph)
            elif f.endswith('.py'):
                _analyze_python_coupling(f, call_graph)
            else:
                # 其他语言的处理
                _analyze_generic_coupling(f, call_graph)
                
        except Exception as e:
            print(f" 分析文件失败: {f} - {e}")
            continue

    # 计算指标
    results = {}
    for f in files:
        # 兼容不同NetworkX版本的度数计算
        try:
            import_deg = import_graph.out_degree(f)
            if hasattr(import_deg, '__iter__') and not isinstance(import_deg, (int, float)):
                import_deg = len(list(import_deg))
            else:
                import_deg = int(import_deg)
        except:
            import_deg = 0
            
        call_deg = sum(1 for n in call_graph.nodes if n.startswith(f + ":"))
        
        # 改进的耦合度计算
        coupling_score = round(import_deg * 0.3 + call_deg * 0.7, 3)
        
        results[f] = {
            "import_coupling": import_deg,
            "call_coupling": call_deg,
            "coupling_score": coupling_score,
            "total_dependencies": import_deg + call_deg
        }
    
    return results


def _analyze_java_coupling(filepath, call_graph):
    """分析Java文件的耦合度"""
    try:
        # 使用AST解析器获取更准确的信息
        parser = get_ast_parser('java')
        ast_info = parser.parse_file(filepath)
        
        # 提取方法和构造函数
        methods = []
        for method_info in ast_info.get('methods', []):
            methods.append(method_info['name'])
        for constructor_info in ast_info.get('constructors', []):
            methods.append(constructor_info['name'])
        
        # 提取方法调用
        calls = parse_java_method_calls(filepath)
        
        # 构建调用图
        for method in methods:
            caller_node = f"{filepath}:{method}"
            for caller, callee in calls:
                if method in caller or caller.startswith(method):
                    call_graph.add_edge(caller_node, callee)
                    
    except Exception as e:
        print(f" Java耦合度分析失败: {filepath} - {e}")


def _analyze_python_coupling(filepath, call_graph):
    """分析Python文件的耦合度"""
    try:
        with open(filepath, "r", encoding="utf-8") as src:
            tree = ast.parse(src.read())
        analyzer = FunctionCallAnalyzer(filepath)
        analyzer.visit(tree)
        for caller, callee in analyzer.calls:
            call_graph.add_edge(f"{filepath}:{caller}", callee)
    except Exception as e:
        print(f" Python耦合度分析失败: {filepath} - {e}")


def _analyze_generic_coupling(filepath, call_graph):
    """分析其他语言文件的耦合度"""
    # 对于其他语言，使用简单的启发式方法
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的函数调用检测
        function_call_pattern = r'(\w+)\s*\('
        matches = re.findall(function_call_pattern, content)
        
        # 假设每个文件有一个主函数
        main_function = os.path.splitext(os.path.basename(filepath))[0]
        caller_node = f"{filepath}:{main_function}"
        
        for callee in matches:
            if callee not in ['if', 'for', 'while', 'switch', 'catch', 'try', 'new', 'return']:
                call_graph.add_edge(caller_node, callee)
                
    except Exception as e:
        print(f" 通用耦合度分析失败: {filepath} - {e}")

# ========= 3️⃣ 耦合度分析与可视化 ==========
def analyze_coupling(coupling_dict, view_type, out_dir):
    """分析单个项目的耦合度"""
    if not coupling_dict:
        print(" 没有耦合度数据可分析")
        return
    
    # 转换为DataFrame
    df = pd.DataFrame([
        {"file": f, **v, "view": view_type} 
        for f, v in coupling_dict.items()
    ])
    
    # 保存报告
    report_csv = Path(out_dir) / "coupling_report.csv"
    ensure_dir(out_dir)
    df.to_csv(report_csv, index=False, encoding="utf-8-sig")
    print(f"耦合度报告已保存至: {report_csv}")
    
    # 计算统计信息
    metrics = ["import_coupling", "call_coupling", "coupling_score"]
    summary = df[metrics].mean()
    
    print(f"=== {view_type} 架构平均耦合度 ===")
    for metric in metrics:
        print(f"{metric}: {summary[metric]:.3f}")
    
    # 生成分布图
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for idx, metric in enumerate(metrics):
        axes[idx].hist(df[metric], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[idx].set_title(f'{metric} 分布')
        axes[idx].set_xlabel(metric)
        axes[idx].set_ylabel('频次')
        axes[idx].axvline(summary[metric], color='red', linestyle='--', 
                         label=f'平均值: {summary[metric]:.2f}')
        axes[idx].legend()
        axes[idx].grid(True, alpha=0.3)
    
    plt.suptitle(f'{view_type} 架构 - 耦合度分布', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # 保存图表
    chart_path = Path(out_dir) / f"{view_type}_coupling_distribution.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"分布图表已保存至: {chart_path}")
    plt.close()

# ========= 4️⃣ 样本处理与划分 ==========
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
    """保存样本并划分训练/验证/测试集"""
    ensure_dir(os.path.dirname(out_prefix))
    
    # 保存完整样本
    with open(out_prefix + ".json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    # 划分训练/验证/测试集 (70/15/15)
    train, temp = train_test_split(samples, test_size=0.3, random_state=42)
    val, test = train_test_split(temp, test_size=0.5, random_state=42)
    
    with open(out_prefix + "_train.json", "w", encoding="utf-8") as f:
        json.dump(train, f, indent=2, ensure_ascii=False)
    with open(out_prefix + "_val.json", "w", encoding="utf-8") as f:
        json.dump(val, f, indent=2, ensure_ascii=False)
    with open(out_prefix + "_test.json", "w", encoding="utf-8") as f:
        json.dump(test, f, indent=2, ensure_ascii=False)
    
    print(f"已划分数据集: 训练集 {len(train)} / 验证集 {len(val)} / 测试集 {len(test)}")

# ========= 主流程 ==========
def main(src_dir, out_dir, view_type):
    """
    主数据构建流程
    
    Args:
        src_dir: 源代码目录
        out_dir: 输出目录
        view_type: 视图类型 ("explicit" 或 "non_explicit")
    """
    print(f"开始{view_type}架构数据构建")
    print(f"源代码目录: {src_dir}")
    print(f"输出目录: {out_dir}")
    print(f"视图类型: {view_type}")
    
    # 1. 生成补全任务样本
    samples = make_completion_samples(src_dir, view_type)
    print(f"生成了 {len(samples)} 个补全任务样本")
    
    # 2. 计算耦合度指标
    coupling = compute_coupling(src_dir)
    print(f"计算了 {len(coupling)} 个文件的耦合度指标")
    
    # 3. 分析耦合度
    analyze_coupling(coupling, view_type, out_dir)
    
    # 4. 附加耦合度信息并保存
    samples = attach_coupling(samples, coupling)
    save_and_split(samples, f"{out_dir}/samples")
    
    print(f"{view_type}架构数据构建完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="直接数据构建脚本")
    parser.add_argument("--src", required=True, help="源代码项目目录")
    parser.add_argument("--out", required=True, help="输出目录")
    parser.add_argument("--view_type", required=True, choices=["explicit", "non_explicit"], 
                       help="视图类型: explicit(显性架构) 或 non_explicit(非显性架构)")
    
    args = parser.parse_args()
    main(args.src, args.out, args.view_type)
