#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_reverse_report.py
----------------------------------------------------
反向对比分析报告生成脚本

功能：
1. 对比MVC架构 vs 显性架构的性能差异
2. 分析耦合度差异
3. 生成可视化对比图表
4. 输出详细的对比分析报告

依赖：
    pip install pandas matplotlib seaborn scipy
----------------------------------------------------
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import ttest_ind
from pathlib import Path
import argparse

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_evaluation_results(eval_dir):
    """加载评估结果"""
    results = {}
    
    # 加载预测结果
    pred_files = {
        'explicit': 'explicit_predictions.jsonl',
        'implicit': 'implicit_predictions.jsonl'
    }
    
    for model_type, filename in pred_files.items():
        filepath = Path(eval_dir) / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                results[model_type] = [json.loads(line) for line in f]
        else:
            print(f"⚠️ 未找到文件: {filepath}")
            results[model_type] = []
    
    return results

def load_coupling_report(coupling_file):
    """加载耦合度报告"""
    if not os.path.exists(coupling_file):
        print(f"⚠️ 未找到耦合度报告: {coupling_file}")
        return None
    
    df = pd.read_csv(coupling_file)
    return df

def calculate_metrics(predictions):
    """计算评估指标"""
    if not predictions:
        return {
            'exact_match': 0.0,
            'total_samples': 0,
            'correct_samples': 0
        }
    
    total = len(predictions)
    correct = sum(1 for p in predictions if p.get('exact_match', False))
    
    return {
        'exact_match': correct / total if total > 0 else 0.0,
        'total_samples': total,
        'correct_samples': correct
    }

def analyze_coupling_difference(mvc_coupling, explicit_coupling):
    """分析耦合度差异"""
    if mvc_coupling is None or explicit_coupling is None:
        return None
    
    # 计算平均耦合度
    mvc_avg = mvc_coupling.groupby('view')[['import_coupling', 'call_coupling', 'coupling_score']].mean()
    explicit_avg = explicit_coupling.groupby('view')[['import_coupling', 'call_coupling', 'coupling_score']].mean()
    
    # 统计检验
    metrics = ['import_coupling', 'call_coupling', 'coupling_score']
    significance_tests = {}
    
    for metric in metrics:
        mvc_values = mvc_coupling[metric].values
        explicit_values = explicit_coupling[metric].values
        
        if len(mvc_values) > 0 and len(explicit_values) > 0:
            t_stat, p_val = ttest_ind(mvc_values, explicit_values, equal_var=False)
            significance_tests[metric] = {
                't_statistic': t_stat,
                'p_value': p_val,
                'significant': p_val < 0.05
            }
    
    return {
        'mvc_averages': mvc_avg.to_dict(),
        'explicit_averages': explicit_avg.to_dict(),
        'significance_tests': significance_tests
    }

def create_comparison_plots(mvc_results, explicit_results, mvc_coupling, explicit_coupling, output_dir):
    """创建对比图表"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 性能对比图
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # 性能指标对比
    mvc_metrics = calculate_metrics(mvc_results.get('explicit', []))
    explicit_metrics = calculate_metrics(explicit_results.get('explicit', []))
    
    models = ['MVC架构', '显性架构']
    exact_match_scores = [mvc_metrics['exact_match'], explicit_metrics['exact_match']]
    
    bars = axes[0].bar(models, exact_match_scores, color=['#ff7f7f', '#7fbf7f'])
    axes[0].set_title('Exact Match 准确率对比', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('准确率')
    axes[0].set_ylim(0, 1)
    
    # 添加数值标签
    for bar, score in zip(bars, exact_match_scores):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. 耦合度对比图
    if mvc_coupling is not None and explicit_coupling is not None:
        # 计算平均耦合度
        mvc_avg_coupling = mvc_coupling['coupling_score'].mean()
        explicit_avg_coupling = explicit_coupling['coupling_score'].mean()
        
        coupling_scores = [mvc_avg_coupling, explicit_avg_coupling]
        bars = axes[1].bar(models, coupling_scores, color=['#ff7f7f', '#7fbf7f'])
        axes[1].set_title('平均耦合度对比', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('耦合度分数')
        
        # 添加数值标签
        for bar, score in zip(bars, coupling_scores):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{score:.2f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path / 'mvc_vs_explicit_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. 耦合度分布对比图
    if mvc_coupling is not None and explicit_coupling is not None:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 创建对比数据
        mvc_data = mvc_coupling['coupling_score'].values
        explicit_data = explicit_coupling['coupling_score'].values
        
        # 箱线图
        data_to_plot = [mvc_data, explicit_data]
        box_plot = ax.boxplot(data_to_plot, labels=models, patch_artist=True)
        
        # 设置颜色
        colors = ['#ff7f7f', '#7fbf7f']
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title('耦合度分布对比', fontsize=14, fontweight='bold')
        ax.set_ylabel('耦合度分数')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / 'coupling_distribution_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

def generate_report(mvc_eval_dir, explicit_eval_dir, mvc_coupling_file, explicit_coupling_file, output_file, output_dir):
    """生成完整的对比分析报告"""
    
    print("📊 加载评估结果...")
    mvc_results = load_evaluation_results(mvc_eval_dir)
    explicit_results = load_evaluation_results(explicit_eval_dir)
    
    print("📊 加载耦合度数据...")
    mvc_coupling = load_coupling_report(mvc_coupling_file)
    explicit_coupling = load_coupling_report(explicit_coupling_file)
    
    print("📊 计算性能指标...")
    mvc_metrics = calculate_metrics(mvc_results.get('explicit', []))
    explicit_metrics = calculate_metrics(explicit_results.get('explicit', []))
    
    print("📊 分析耦合度差异...")
    coupling_analysis = analyze_coupling_difference(mvc_coupling, explicit_coupling)
    
    print("📊 生成对比图表...")
    create_comparison_plots(mvc_results, explicit_results, mvc_coupling, explicit_coupling, output_dir)
    
    # 生成报告
    report = {
        'experiment_type': 'MVC架构 vs 显性架构对比',
        'summary': {
            'mvc_architecture': {
                'exact_match_accuracy': mvc_metrics['exact_match'],
                'total_samples': mvc_metrics['total_samples'],
                'correct_samples': mvc_metrics['correct_samples']
            },
            'explicit_architecture': {
                'exact_match_accuracy': explicit_metrics['exact_match'],
                'total_samples': explicit_metrics['total_samples'],
                'correct_samples': explicit_metrics['correct_samples']
            },
            'performance_difference': {
                'accuracy_delta': explicit_metrics['exact_match'] - mvc_metrics['exact_match'],
                'improvement_percentage': ((explicit_metrics['exact_match'] - mvc_metrics['exact_match']) / mvc_metrics['exact_match'] * 100) if mvc_metrics['exact_match'] > 0 else 0
            }
        },
        'coupling_analysis': coupling_analysis,
        'conclusions': {
            'performance': '显性架构在函数补全任务上表现更好' if explicit_metrics['exact_match'] > mvc_metrics['exact_match'] else 'MVC架构在函数补全任务上表现更好',
            'coupling': '显性架构具有更低的耦合度' if coupling_analysis and coupling_analysis['explicit_averages'].get('coupling_score', {}).get('explicit', 0) < coupling_analysis['mvc_averages'].get('coupling_score', {}).get('explicit', 0) else 'MVC架构具有更低的耦合度'
        }
    }
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 对比分析报告已生成: {output_file}")
    print(f"📊 图表已保存到: {output_dir}")
    
    # 打印关键结果
    print("\n🎯 关键结果:")
    print(f"   MVC架构准确率: {mvc_metrics['exact_match']:.3f}")
    print(f"   显性架构准确率: {explicit_metrics['exact_match']:.3f}")
    print(f"   性能提升: {report['summary']['performance_difference']['improvement_percentage']:.1f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成MVC架构 vs 显性架构对比分析报告")
    parser.add_argument("--mvc_eval", required=True, help="MVC架构评估结果目录")
    parser.add_argument("--explicit_eval", required=True, help="显性架构评估结果目录")
    parser.add_argument("--mvc_coupling", required=True, help="MVC架构耦合度报告文件")
    parser.add_argument("--explicit_coupling", required=True, help="显性架构耦合度报告文件")
    parser.add_argument("--output", required=True, help="输出报告文件")
    parser.add_argument("--output_dir", required=True, help="输出目录")
    
    args = parser.parse_args()
    
    generate_report(
        args.mvc_eval,
        args.explicit_eval,
        args.mvc_coupling,
        args.explicit_coupling,
        args.output,
        args.output_dir
    )
