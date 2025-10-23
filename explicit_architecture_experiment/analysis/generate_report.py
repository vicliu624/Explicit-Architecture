#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_report.py
----------------------------------------------------
实验报告生成器

功能：
1. 整合所有实验结果
2. 生成综合分析报告
3. 输出可视化图表
4. 生成结论和建议

依赖：
    pip install pandas matplotlib seaborn scipy
----------------------------------------------------
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse


class ExperimentReportGenerator:
    """实验报告生成器"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.ensure_dir(output_dir)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
    def ensure_dir(self, path: str):
        """确保目录存在"""
        os.makedirs(path, exist_ok=True)
    
    def load_evaluation_results(self, explicit_eval_file: str, implicit_eval_file: str) -> Dict[str, Any]:
        """加载评估结果"""
        print("📊 加载评估结果...")
        
        # 加载显性架构评估结果
        explicit_results = []
        with open(explicit_eval_file, 'r', encoding='utf-8') as f:
            for line in f:
                explicit_results.append(json.loads(line.strip()))
        
        # 加载非显性架构评估结果
        implicit_results = []
        with open(implicit_eval_file, 'r', encoding='utf-8') as f:
            for line in f:
                implicit_results.append(json.loads(line.strip()))
        
        # 计算性能指标
        explicit_metrics = self._compute_metrics(explicit_results)
        implicit_metrics = self._compute_metrics(implicit_results)
        
        # 统计检验
        comparison_results = self._compare_metrics(explicit_metrics, implicit_metrics)
        
        return {
            'explicit_metrics': explicit_metrics,
            'implicit_metrics': implicit_metrics,
            'comparison': comparison_results
        }
    
    def load_coupling_analysis(self, coupling_report_file: str) -> Dict[str, Any]:
        """加载耦合度分析结果"""
        print("🔍 加载耦合度分析...")
        
        # 加载CSV报告
        df = pd.read_csv(coupling_report_file)
        
        # 按架构类型分组
        explicit_df = df[df['view'] == 'explicit']
        implicit_df = df[df['view'] == 'non_explicit']
        
        # 计算统计指标
        metrics = ['import_coupling', 'call_coupling', 'coupling_score']
        results = {}
        
        for metric in metrics:
            if metric in df.columns:
                exp_values = explicit_df[metric].values
                imp_values = implicit_df[metric].values
                
                # 统计检验
                t_stat, t_p = stats.ttest_ind(exp_values, imp_values)
                u_stat, u_p = stats.mannwhitneyu(exp_values, imp_values, alternative='two-sided')
                
                results[metric] = {
                    'explicit_mean': np.mean(exp_values),
                    'explicit_std': np.std(exp_values),
                    'implicit_mean': np.mean(imp_values),
                    'implicit_std': np.std(imp_values),
                    'difference': np.mean(exp_values) - np.mean(imp_values),
                    't_statistic': t_stat,
                    't_p_value': t_p,
                    'u_statistic': u_stat,
                    'u_p_value': u_p
                }
        
        return results
    
    def load_attention_analysis(self, attention_analysis_dir: str) -> Dict[str, Any]:
        """加载注意力分析结果"""
        print("🧠 加载注意力分析...")
        
        # 加载注意力统计结果
        stats_file = os.path.join(attention_analysis_dir, "attention_statistics.json")
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    
    def load_probe_analysis(self, probe_analysis_dir: str) -> Dict[str, Any]:
        """加载探针分析结果"""
        print("🧪 加载探针分析...")
        
        # 加载探针统计结果
        stats_file = os.path.join(probe_analysis_dir, "probe_statistics.json")
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    
    def _compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算性能指标"""
        if not results:
            return {}
        
        metrics = {}
        
        # 基本指标
        if 'exact_match' in results[0]:
            exact_matches = [r['exact_match'] for r in results]
            metrics['exact_match_rate'] = np.mean(exact_matches)
            metrics['exact_match_std'] = np.std(exact_matches)
        
        if 'bleu' in results[0]:
            bleu_scores = [r['bleu'] for r in results]
            metrics['bleu_mean'] = np.mean(bleu_scores)
            metrics['bleu_std'] = np.std(bleu_scores)
        
        if 'rouge1' in results[0]:
            rouge1_scores = [r['rouge1'] for r in results]
            metrics['rouge1_mean'] = np.mean(rouge1_scores)
            metrics['rouge1_std'] = np.std(rouge1_scores)
        
        if 'rougeL' in results[0]:
            rougeL_scores = [r['rougeL'] for r in results]
            metrics['rougeL_mean'] = np.mean(rougeL_scores)
            metrics['rougeL_std'] = np.std(rougeL_scores)
        
        if 'meteor' in results[0]:
            meteor_scores = [r['meteor'] for r in results]
            metrics['meteor_mean'] = np.mean(meteor_scores)
            metrics['meteor_std'] = np.std(meteor_scores)
        
        return metrics
    
    def _compare_metrics(self, explicit_metrics: Dict[str, float], 
                        implicit_metrics: Dict[str, float]) -> Dict[str, Any]:
        """比较指标"""
        comparison = {}
        
        for metric in explicit_metrics.keys():
            if metric in implicit_metrics:
                exp_values = [explicit_metrics[metric]]
                imp_values = [implicit_metrics[metric]]
                
                # 简单的比较（实际应用中需要更多样本）
                comparison[metric] = {
                    'explicit_value': explicit_metrics[metric],
                    'implicit_value': implicit_metrics[metric],
                    'difference': explicit_metrics[metric] - implicit_metrics[metric],
                    'improvement': (explicit_metrics[metric] - implicit_metrics[metric]) / implicit_metrics[metric] * 100
                }
        
        return comparison
    
    def generate_comprehensive_report(self, evaluation_results: Dict[str, Any],
                                    coupling_results: Dict[str, Any],
                                    attention_results: Dict[str, Any],
                                    probe_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合报告"""
        print("📋 生成综合报告...")
        
        report = {
            'experiment_summary': {
                'title': '显性架构实验综合报告',
                'date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_metrics_analyzed': 0,
                'significant_differences': 0,
                'overall_conclusion': ''
            },
            'performance_analysis': evaluation_results,
            'coupling_analysis': coupling_results,
            'attention_analysis': attention_results,
            'probe_analysis': probe_results,
            'conclusions_and_recommendations': {}
        }
        
        # 统计显著差异
        significant_count = 0
        total_metrics = 0
        
        # 性能指标
        if 'comparison' in evaluation_results:
            for metric, comparison in evaluation_results['comparison'].items():
                total_metrics += 1
                if 't_p_value' in comparison and comparison['t_p_value'] < 0.05:
                    significant_count += 1
        
        # 耦合度指标
        for metric, results in coupling_results.items():
            total_metrics += 1
            if results['t_p_value'] < 0.05:
                significant_count += 1
        
        # 注意力指标
        if attention_results:
            total_metrics += 2  # entropy 和 concentration
            if 'entropy_comparison' in attention_results and attention_results['entropy_comparison']['t_p_value'] < 0.05:
                significant_count += 1
            if 'concentration_comparison' in attention_results and attention_results['concentration_comparison']['t_p_value'] < 0.05:
                significant_count += 1
        
        # 探针指标
        if probe_results:
            total_metrics += 1
            if 'accuracy_comparison' in probe_results and probe_results['accuracy_comparison']['t_p_value'] < 0.05:
                significant_count += 1
        
        report['experiment_summary']['total_metrics_analyzed'] = total_metrics
        report['experiment_summary']['significant_differences'] = significant_count
        
        # 生成结论
        conclusions = self._generate_conclusions(report)
        report['conclusions_and_recommendations'] = conclusions
        
        return report
    
    def _generate_conclusions(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """生成结论和建议"""
        conclusions = {
            'key_findings': [],
            'statistical_significance': {},
            'practical_implications': [],
            'limitations': [],
            'future_work': []
        }
        
        # 关键发现
        significant_count = report['experiment_summary']['significant_differences']
        total_metrics = report['experiment_summary']['total_metrics_analyzed']
        
        if significant_count > total_metrics * 0.5:
            conclusions['key_findings'].append("显性架构在多个维度上显著优于非显性架构")
        elif significant_count > 0:
            conclusions['key_findings'].append("显性架构在部分维度上优于非显性架构")
        else:
            conclusions['key_findings'].append("显性架构和非显性架构没有显著差异")
        
        # 统计显著性
        conclusions['statistical_significance'] = {
            'significant_metrics': significant_count,
            'total_metrics': total_metrics,
            'significance_rate': significant_count / total_metrics if total_metrics > 0 else 0
        }
        
        # 实际意义
        if significant_count > 0:
            conclusions['practical_implications'].append("建议在软件开发中采用显性架构设计原则")
            conclusions['practical_implications'].append("显性架构有助于提升AI模型在代码理解任务上的性能")
        
        # 局限性
        conclusions['limitations'].append("实验样本数量有限")
        conclusions['limitations'].append("主要针对Python代码，其他语言需要进一步验证")
        conclusions['limitations'].append("模型规模相对较小，大规模模型的效果需要进一步研究")
        
        # 未来工作
        conclusions['future_work'].append("扩展到更多编程语言和项目类型")
        conclusions['future_work'].append("使用更大规模的预训练模型")
        conclusions['future_work'].append("研究显性架构在不同代码任务上的效果")
        conclusions['future_work'].append("开发自动化的显性架构检测和优化工具")
        
        return conclusions
    
    def create_visualizations(self, report: Dict[str, Any]):
        """创建可视化图表"""
        print("📊 创建可视化图表...")
        
        # 1. 性能对比图
        self._create_performance_comparison_chart(report)
        
        # 2. 耦合度对比图
        self._create_coupling_comparison_chart(report)
        
        # 3. 综合结果图
        self._create_comprehensive_results_chart(report)
    
    def _create_performance_comparison_chart(self, report: Dict[str, Any]):
        """创建性能对比图"""
        if 'performance_analysis' not in report:
            return
        
        performance = report['performance_analysis']
        if 'comparison' not in performance:
            return
        
        # 提取数据
        metrics = list(performance['comparison'].keys())
        explicit_values = [performance['comparison'][m]['explicit_value'] for m in metrics]
        implicit_values = [performance['comparison'][m]['implicit_value'] for m in metrics]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(len(metrics))
        width = 0.35
        
        ax.bar(x - width/2, explicit_values, width, label='显性架构', alpha=0.8)
        ax.bar(x + width/2, implicit_values, width, label='非显性架构', alpha=0.8)
        
        ax.set_xlabel('性能指标')
        ax.set_ylabel('分数')
        ax.set_title('显性架构 vs 非显性架构 - 性能对比')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'performance_comparison.png'), 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def _create_coupling_comparison_chart(self, report: Dict[str, Any]):
        """创建耦合度对比图"""
        if 'coupling_analysis' not in report:
            return
        
        coupling = report['coupling_analysis']
        
        # 提取数据
        metrics = list(coupling.keys())
        explicit_means = [coupling[m]['explicit_mean'] for m in metrics]
        implicit_means = [coupling[m]['implicit_mean'] for m in metrics]
        explicit_stds = [coupling[m]['explicit_std'] for m in metrics]
        implicit_stds = [coupling[m]['implicit_std'] for m in metrics]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(len(metrics))
        width = 0.35
        
        ax.bar(x - width/2, explicit_means, width, yerr=explicit_stds, 
               label='显性架构', alpha=0.8, capsize=5)
        ax.bar(x + width/2, implicit_means, width, yerr=implicit_stds, 
              label='非显性架构', alpha=0.8, capsize=5)
        
        ax.set_xlabel('耦合度指标')
        ax.set_ylabel('耦合度分数')
        ax.set_title('显性架构 vs 非显性架构 - 耦合度对比')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'coupling_comparison.png'), 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def _create_comprehensive_results_chart(self, report: Dict[str, Any]):
        """创建综合结果图"""
        # 创建总结图表
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 显著差异统计
        significant_count = report['experiment_summary']['significant_differences']
        total_metrics = report['experiment_summary']['total_metrics_analyzed']
        
        axes[0, 0].pie([significant_count, total_metrics - significant_count], 
                      labels=['显著差异', '无显著差异'], 
                      autopct='%1.1f%%', startangle=90)
        axes[0, 0].set_title('统计显著性分布')
        
        # 2. 性能提升百分比
        if 'performance_analysis' in report and 'comparison' in report['performance_analysis']:
            improvements = []
            for metric, comparison in report['performance_analysis']['comparison'].items():
                if 'improvement' in comparison:
                    improvements.append(comparison['improvement'])
            
            if improvements:
                axes[0, 1].bar(range(len(improvements)), improvements, alpha=0.7)
                axes[0, 1].set_title('性能提升百分比')
                axes[0, 1].set_ylabel('提升百分比 (%)')
                axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 耦合度差异
        if 'coupling_analysis' in report:
            differences = []
            for metric, results in report['coupling_analysis'].items():
                differences.append(results['difference'])
            
            axes[1, 0].bar(range(len(differences)), differences, alpha=0.7)
            axes[1, 0].set_title('耦合度差异')
            axes[1, 0].set_ylabel('差异值')
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 实验总结
        axes[1, 1].text(0.1, 0.5, f"""
        实验总结:
        
        总指标数: {total_metrics}
        显著差异: {significant_count}
        显著性率: {significant_count/total_metrics*100:.1f}%
        
        结论: {'显性架构显著优于非显性架构' if significant_count > total_metrics*0.5 else '需要更多证据'}
        """, fontsize=12, verticalalignment='center',
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        axes[1, 1].set_title('实验总结')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'comprehensive_results.png'), 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_report(self, report: Dict[str, Any], output_file: str):
        """保存报告"""
        print(f"💾 保存报告到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("✅ 报告保存完成!")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成显性架构实验报告")
    parser.add_argument("--explicit_eval", type=str, required=True,
                       help="显性架构评估结果文件")
    parser.add_argument("--implicit_eval", type=str, required=True,
                       help="非显性架构评估结果文件")
    parser.add_argument("--coupling_report", type=str, required=True,
                       help="耦合度报告文件")
    parser.add_argument("--attention_analysis", type=str, required=True,
                       help="注意力分析结果目录")
    parser.add_argument("--probe_analysis", type=str, required=True,
                       help="探针分析结果目录")
    parser.add_argument("--output", type=str, default="./final_report.json",
                       help="输出报告文件")
    parser.add_argument("--output_dir", type=str, default="./report_output",
                       help="输出目录")
    
    args = parser.parse_args()
    
    # 创建报告生成器
    generator = ExperimentReportGenerator(args.output_dir)
    
    # 加载所有结果
    evaluation_results = generator.load_evaluation_results(args.explicit_eval, args.implicit_eval)
    coupling_results = generator.load_coupling_analysis(args.coupling_report)
    attention_results = generator.load_attention_analysis(args.attention_analysis)
    probe_results = generator.load_probe_analysis(args.probe_analysis)
    
    # 生成综合报告
    comprehensive_report = generator.generate_comprehensive_report(
        evaluation_results, coupling_results, attention_results, probe_results
    )
    
    # 创建可视化
    generator.create_visualizations(comprehensive_report)
    
    # 保存报告
    generator.save_report(comprehensive_report, args.output)
    
    print("🎯 实验报告生成完成!")
    print(f"📊 报告文件: {args.output}")
    print(f"📈 图表目录: {args.output_dir}")


if __name__ == "__main__":
    main()
