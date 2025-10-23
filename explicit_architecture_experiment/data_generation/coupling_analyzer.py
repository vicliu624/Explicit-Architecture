#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coupling_analyzer.py
----------------------------------------------------
函数耦合度分析工具

功能：
1. 基于AST分析函数调用关系
2. 计算多种耦合度指标
3. 生成耦合度报告和可视化
4. 支持不同编程语言的耦合度分析

依赖：
    pip install astor networkx matplotlib seaborn
----------------------------------------------------
"""

import os
import ast
import json
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict


class CouplingAnalyzer:
    """函数耦合度分析器"""
    
    def __init__(self, language="python"):
        self.language = language
        self.call_graph = nx.DiGraph()
        self.import_graph = nx.DiGraph()
        self.function_index = {}  # {function_name: file_path}
        self.file_functions = defaultdict(list)  # {file_path: [function_names]}
        
    def analyze_project(self, project_dir: str) -> Dict[str, Any]:
        """
        分析整个项目的耦合度
        
        Args:
            project_dir: 项目目录路径
            
        Returns:
            dict: 耦合度分析结果
        """
        print(f"🔍 开始分析项目耦合度: {project_dir}")
        
        # 清空之前的分析结果
        self.call_graph.clear()
        self.import_graph.clear()
        self.function_index.clear()
        self.file_functions.clear()
        
        # 获取所有源文件
        source_files = self._get_source_files(project_dir)
        print(f"📄 发现 {len(source_files)} 个源文件")
        
        # 第一遍：建立函数索引
        for file_path in source_files:
            self._index_functions(file_path)
        
        # 第二遍：分析调用关系
        for file_path in source_files:
            self._analyze_file_coupling(file_path)
        
        # 计算耦合度指标
        coupling_metrics = self._compute_coupling_metrics()
        
        # 生成分析报告
        report = self._generate_report(coupling_metrics)
        
        print(f"✅ 耦合度分析完成")
        return report
    
    def _get_source_files(self, project_dir: str) -> List[str]:
        """获取项目中的所有源文件"""
        source_files = []
        supported_extensions = ['.py', '.java', '.js', '.ts', '.cpp', '.c', '.cs', '.go', '.rs']
        for root, _, files in os.walk(project_dir):
            for file in files:
                if any(file.endswith(ext) for ext in supported_extensions):
                    source_files.append(os.path.join(root, file))
        return source_files
    
    def _index_functions(self, file_path: str):
        """建立函数索引"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('.py'):
                self._index_python_functions(file_path, content)
            # 可以扩展支持其他语言
                
        except Exception as e:
            print(f"⚠️ 索引函数失败: {file_path} - {e}")
    
    def _index_python_functions(self, file_path: str, content: str):
        """索引Python函数"""
        try:
            tree = ast.parse(content, filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    full_name = f"{file_path}:{func_name}"
                    self.function_index[func_name] = file_path
                    self.file_functions[file_path].append(func_name)
                    self.call_graph.add_node(full_name)
        except SyntaxError:
            print(f"⚠️ 语法错误，跳过文件: {file_path}")
    
    def _analyze_file_coupling(self, file_path: str):
        """分析文件的耦合度"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('.py'):
                self._analyze_python_coupling(file_path, content)
                
        except Exception as e:
            print(f"⚠️ 分析耦合度失败: {file_path} - {e}")
    
    def _analyze_python_coupling(self, file_path: str, content: str):
        """分析Python文件的耦合度"""
        try:
            tree = ast.parse(content, filename=file_path)
            
            # 分析导入关系
            self._analyze_imports(file_path, tree)
            
            # 分析函数调用关系
            self._analyze_function_calls(file_path, tree)
                
        except SyntaxError:
            print(f"⚠️ 语法错误，跳过文件: {file_path}")
    
    def _analyze_imports(self, file_path: str, tree: ast.AST):
        """分析导入关系"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.import_graph.add_edge(file_path, alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.import_graph.add_edge(file_path, node.module)
    
    def _analyze_function_calls(self, file_path: str, tree: ast.AST):
        """分析函数调用关系"""
        class CallVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, file_path):
                self.analyzer = analyzer
                self.file_path = file_path
                self.current_function = None
            
            def visit_FunctionDef(self, node):
                prev_func = self.current_function
                self.current_function = node.name
                self.generic_visit(node)
                self.current_function = prev_func
            
            def visit_Call(self, node):
                if self.current_function:
                    # 获取被调用函数名
                    if isinstance(node.func, ast.Name):
                        callee = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        callee = ast.unparse(node.func)
                    else:
                        callee = "unknown"
                    
                    # 建立调用关系
                    caller = f"{self.file_path}:{self.current_function}"
                    if callee in self.analyzer.function_index:
                        callee_file = self.analyzer.function_index[callee]
                        callee_full = f"{callee_file}:{callee}"
                        self.analyzer.call_graph.add_edge(caller, callee_full)
                
                self.generic_visit(node)
        
        visitor = CallVisitor(self, file_path)
        visitor.visit(tree)
    
    def _compute_coupling_metrics(self) -> Dict[str, Any]:
        """计算耦合度指标"""
        metrics = {}
        
        for file_path in self.file_functions:
            # 文件级指标
            import_in = self.import_graph.in_degree(file_path)
            import_out = self.import_graph.out_degree(file_path)
            
            # 函数级指标
            file_functions = self.file_functions[file_path]
            fan_in_total = 0
            fan_out_total = 0
            
            for func_name in file_functions:
                func_node = f"{file_path}:{func_name}"
                fan_in = self.call_graph.in_degree(func_node)
                fan_out = self.call_graph.out_degree(func_node)
                fan_in_total += fan_in
                fan_out_total += fan_out
            
            # 计算综合耦合度
            coupling_score = import_in * 0.2 + import_out * 0.2 + fan_in_total * 0.3 + fan_out_total * 0.3
            
            metrics[file_path] = {
                "import_in": import_in,
                "import_out": import_out,
                "fan_in_total": fan_in_total,
                "fan_out_total": fan_out_total,
                "coupling_score": round(coupling_score, 3),
                "function_count": len(file_functions)
            }
        
        return metrics
    
    def _generate_report(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成分析报告"""
        # 计算统计指标
        coupling_scores = [m["coupling_score"] for m in metrics.values()]
        import_in_scores = [m["import_in"] for m in metrics.values()]
        import_out_scores = [m["import_out"] for m in metrics.values()]
        fan_in_scores = [m["fan_in_total"] for m in metrics.values()]
        fan_out_scores = [m["fan_out_total"] for m in metrics.values()]
        
        report = {
            "summary": {
                "total_files": len(metrics),
                "total_functions": sum(m["function_count"] for m in metrics.values()),
                "avg_coupling_score": np.mean(coupling_scores),
                "max_coupling_score": np.max(coupling_scores),
                "min_coupling_score": np.min(coupling_scores),
                "std_coupling_score": np.std(coupling_scores)
            },
            "metrics": metrics,
            "statistics": {
                "coupling_score": {
                    "mean": np.mean(coupling_scores),
                    "std": np.std(coupling_scores),
                    "median": np.median(coupling_scores),
                    "q25": np.percentile(coupling_scores, 25),
                    "q75": np.percentile(coupling_scores, 75)
                },
                "import_in": {
                    "mean": np.mean(import_in_scores),
                    "std": np.std(import_in_scores)
                },
                "import_out": {
                    "mean": np.mean(import_out_scores),
                    "std": np.std(import_out_scores)
                },
                "fan_in": {
                    "mean": np.mean(fan_in_scores),
                    "std": np.std(fan_in_scores)
                },
                "fan_out": {
                    "mean": np.mean(fan_out_scores),
                    "std": np.std(fan_out_scores)
                }
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """保存分析报告"""
        ensure_dir(os.path.dirname(output_path))
        
        # 保存JSON报告
        json_path = output_path.replace('.csv', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存CSV报告
        df_data = []
        for file_path, metrics in report["metrics"].items():
            row = {"file": file_path}
            row.update(metrics)
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"📊 耦合度报告已保存:")
        print(f"   JSON: {json_path}")
        print(f"   CSV: {output_path}")
    
    def visualize_coupling(self, report: Dict[str, Any], output_dir: str):
        """可视化耦合度分析结果"""
        ensure_dir(output_dir)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 耦合度分布直方图
        coupling_scores = [m["coupling_score"] for m in report["metrics"].values()]
        
        plt.figure(figsize=(12, 8))
        
        # 子图1: 耦合度分布
        plt.subplot(2, 2, 1)
        plt.hist(coupling_scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.xlabel('耦合度分数')
        plt.ylabel('文件数量')
        plt.title('耦合度分布直方图')
        plt.grid(True, alpha=0.3)
        
        # 子图2: 导入关系散点图
        plt.subplot(2, 2, 2)
        import_in = [m["import_in"] for m in report["metrics"].values()]
        import_out = [m["import_out"] for m in report["metrics"].values()]
        plt.scatter(import_in, import_out, alpha=0.6, color='lightcoral')
        plt.xlabel('导入入度')
        plt.ylabel('导入出度')
        plt.title('导入关系散点图')
        plt.grid(True, alpha=0.3)
        
        # 子图3: 函数调用关系散点图
        plt.subplot(2, 2, 3)
        fan_in = [m["fan_in_total"] for m in report["metrics"].values()]
        fan_out = [m["fan_out_total"] for m in report["metrics"].values()]
        plt.scatter(fan_in, fan_out, alpha=0.6, color='lightgreen')
        plt.xlabel('函数调用入度')
        plt.ylabel('函数调用出度')
        plt.title('函数调用关系散点图')
        plt.grid(True, alpha=0.3)
        
        # 子图4: 耦合度箱线图
        plt.subplot(2, 2, 4)
        plt.boxplot(coupling_scores, patch_artist=True, 
                   boxprops=dict(facecolor='lightblue', alpha=0.7))
        plt.ylabel('耦合度分数')
        plt.title('耦合度箱线图')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = os.path.join(output_dir, "coupling_analysis.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"📈 耦合度分析图表已保存: {chart_path}")
        plt.show()
    
    def compare_architectures(self, explicit_report: Dict[str, Any], 
                            implicit_report: Dict[str, Any], 
                            output_dir: str):
        """比较显性和非显性架构的耦合度差异"""
        ensure_dir(output_dir)
        
        # 提取耦合度数据
        exp_scores = [m["coupling_score"] for m in explicit_report["metrics"].values()]
        imp_scores = [m["coupling_score"] for m in implicit_report["metrics"].values()]
        
        # 统计检验
        from scipy.stats import ttest_ind, mannwhitneyu
        
        t_stat, t_p = ttest_ind(exp_scores, imp_scores)
        u_stat, u_p = mannwhitneyu(exp_scores, imp_scores, alternative='two-sided')
        
        # 计算效应量
        from scipy.stats import cohen_d
        effect_size = cohen_d(exp_scores, imp_scores)
        
        # 创建对比图
        plt.figure(figsize=(15, 10))
        
        # 子图1: 箱线图对比
        plt.subplot(2, 3, 1)
        data_to_plot = [exp_scores, imp_scores]
        labels = ['显性架构', '非显性架构']
        plt.boxplot(data_to_plot, labels=labels, patch_artist=True,
                   boxprops=dict(facecolor='lightblue', alpha=0.7),
                   medianprops=dict(color='red', linewidth=2))
        plt.ylabel('耦合度分数')
        plt.title('架构耦合度对比')
        plt.grid(True, alpha=0.3)
        
        # 子图2: 直方图对比
        plt.subplot(2, 3, 2)
        plt.hist(exp_scores, bins=15, alpha=0.7, label='显性架构', color='skyblue')
        plt.hist(imp_scores, bins=15, alpha=0.7, label='非显性架构', color='lightcoral')
        plt.xlabel('耦合度分数')
        plt.ylabel('文件数量')
        plt.title('耦合度分布对比')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 子图3: 平均值对比
        plt.subplot(2, 3, 3)
        means = [np.mean(exp_scores), np.mean(imp_scores)]
        stds = [np.std(exp_scores), np.std(imp_scores)]
        x_pos = [0, 1]
        plt.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7, 
               color=['skyblue', 'lightcoral'])
        plt.xticks(x_pos, labels)
        plt.ylabel('平均耦合度')
        plt.title('平均耦合度对比')
        plt.grid(True, alpha=0.3)
        
        # 子图4: 累积分布函数
        plt.subplot(2, 3, 4)
        exp_sorted = np.sort(exp_scores)
        imp_sorted = np.sort(imp_scores)
        exp_cdf = np.arange(1, len(exp_sorted) + 1) / len(exp_sorted)
        imp_cdf = np.arange(1, len(imp_sorted) + 1) / len(imp_sorted)
        plt.plot(exp_sorted, exp_cdf, label='显性架构', linewidth=2)
        plt.plot(imp_sorted, imp_cdf, label='非显性架构', linewidth=2)
        plt.xlabel('耦合度分数')
        plt.ylabel('累积概率')
        plt.title('累积分布函数')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 子图5: 散点图
        plt.subplot(2, 3, 5)
        plt.scatter(range(len(exp_scores)), exp_scores, alpha=0.6, 
                   label='显性架构', color='skyblue')
        plt.scatter(range(len(imp_scores)), imp_scores, alpha=0.6, 
                   label='非显性架构', color='lightcoral')
        plt.xlabel('文件索引')
        plt.ylabel('耦合度分数')
        plt.title('耦合度散点图')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 子图6: 统计信息
        plt.subplot(2, 3, 6)
        plt.axis('off')
        stats_text = f"""
        统计检验结果:
        
        t检验:
        t统计量: {t_stat:.4f}
        p值: {t_p:.4f}
        
        Mann-Whitney U检验:
        U统计量: {u_stat:.4f}
        p值: {u_p:.4f}
        
        效应量 (Cohen's d):
        {effect_size:.4f}
        
        样本量:
        显性架构: {len(exp_scores)}
        非显性架构: {len(imp_scores)}
        """
        plt.text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        
        plt.tight_layout()
        
        # 保存对比图
        comparison_path = os.path.join(output_dir, "architecture_comparison.png")
        plt.savefig(comparison_path, dpi=300, bbox_inches='tight')
        print(f"📊 架构对比图已保存: {comparison_path}")
        plt.show()
        
        # 打印统计结果
        print(f"\n📊 统计检验结果:")
        print(f"   t检验: t={t_stat:.4f}, p={t_p:.4f}")
        print(f"   Mann-Whitney U检验: U={u_stat:.4f}, p={u_p:.4f}")
        print(f"   效应量 (Cohen's d): {effect_size:.4f}")
        print(f"   显性架构平均耦合度: {np.mean(exp_scores):.3f} ± {np.std(exp_scores):.3f}")
        print(f"   非显性架构平均耦合度: {np.mean(imp_scores):.3f} ± {np.std(imp_scores):.3f}")


def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description="函数耦合度分析工具")
    parser.add_argument("--explicit_dir", required=True, help="显性架构项目目录")
    parser.add_argument("--implicit_dir", required=True, help="非显性架构项目目录")
    parser.add_argument("--output_dir", default="./coupling_analysis", help="输出目录")
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = CouplingAnalyzer()
    
    # 分析显性架构
    print("🔍 分析显性架构耦合度...")
    explicit_report = analyzer.analyze_project(args.explicit_dir)
    analyzer.save_report(explicit_report, os.path.join(args.output_dir, "explicit_coupling.csv"))
    analyzer.visualize_coupling(explicit_report, args.output_dir)
    
    # 分析非显性架构
    print("🔍 分析非显性架构耦合度...")
    implicit_report = analyzer.analyze_project(args.implicit_dir)
    analyzer.save_report(implicit_report, os.path.join(args.output_dir, "implicit_coupling.csv"))
    
    # 比较两种架构
    print("📊 比较两种架构的耦合度差异...")
    analyzer.compare_architectures(explicit_report, implicit_report, args.output_dir)
    
    print("✅ 耦合度分析完成!")


if __name__ == "__main__":
    main()
