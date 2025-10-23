#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
attention_extractor.py
----------------------------------------------------
注意力机制分析工具

功能：
1. 提取模型各层的注意力矩阵
2. 分析注意力模式差异
3. 计算注意力熵和集中度指标
4. 可视化注意力分布

依赖：
    pip install transformers torch matplotlib seaborn
----------------------------------------------------
"""

import os
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from tqdm import tqdm
import argparse

from transformers import AutoModelForCausalLM, AutoTokenizer


class AttentionAnalyzer:
    """注意力机制分析器"""
    
    def __init__(self, model_path: str, device: str = "auto"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        """加载模型和tokenizer"""
        print(f"🔧 加载模型: {self.model_path}")
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            use_fast=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 加载模型（启用注意力输出）
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=self.device,
            output_attentions=True
        )
        
        print(f"✅ 模型加载完成")
        print(f"   层数: {self.model.config.n_layer}")
        print(f"   注意力头数: {self.model.config.n_head}")
    
    def extract_attention(self, text: str, max_length: int = 512) -> Dict[str, np.ndarray]:
        """提取文本的注意力矩阵"""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        ).to(self.model.device)
        
        # 前向传播
        with torch.no_grad():
            outputs = self.model(**inputs, output_attentions=True)
        
        # 提取注意力矩阵
        attentions = outputs.attentions  # tuple of (layer, batch, head, seq, seq)
        
        # 转换为numpy数组
        attention_matrices = {}
        for layer_idx, attention in enumerate(attentions):
            # attention shape: (batch, head, seq, seq)
            attention_np = attention[0].cpu().numpy()  # 移除batch维度
            attention_matrices[f"layer_{layer_idx}"] = attention_np
        
        return attention_matrices
    
    def compute_attention_entropy(self, attention_matrix: np.ndarray) -> float:
        """计算注意力熵"""
        # attention_matrix shape: (head, seq, seq)
        # 对每个token计算其注意力分布的熵
        entropies = []
        for head_idx in range(attention_matrix.shape[0]):
            for token_idx in range(attention_matrix.shape[1]):
                attention_dist = attention_matrix[head_idx, token_idx, :]
                # 归一化
                attention_dist = attention_dist / (attention_dist.sum() + 1e-8)
                # 计算熵
                entropy = -np.sum(attention_dist * np.log(attention_dist + 1e-8))
                entropies.append(entropy)
        
        return np.mean(entropies)
    
    def compute_attention_concentration(self, attention_matrix: np.ndarray) -> float:
        """计算注意力集中度"""
        # 计算注意力权重的集中程度
        # 使用Gini系数或最大注意力比例
        concentrations = []
        for head_idx in range(attention_matrix.shape[0]):
            for token_idx in range(attention_matrix.shape[1]):
                attention_dist = attention_matrix[head_idx, token_idx, :]
                # 归一化
                attention_dist = attention_dist / (attention_dist.sum() + 1e-8)
                # 计算最大注意力比例
                max_attention = np.max(attention_dist)
                concentrations.append(max_attention)
        
        return np.mean(concentrations)
    
    def compute_module_attention_mass(self, attention_matrix: np.ndarray, 
                                    module_boundaries: List[Tuple[int, int]]) -> float:
        """计算模块内注意力质量"""
        if not module_boundaries:
            return 0.0
        
        total_mass = 0.0
        module_mass = 0.0
        
        for head_idx in range(attention_matrix.shape[0]):
            for token_idx in range(attention_matrix.shape[1]):
                attention_dist = attention_matrix[head_idx, token_idx, :]
                total_mass += attention_dist.sum()
                
                # 计算模块内注意力
                for start, end in module_boundaries:
                    if start <= token_idx < end:
                        module_mass += attention_dist[start:end].sum()
                        break
        
        return module_mass / (total_mass + 1e-8)
    
    def analyze_attention_patterns(self, attention_matrices: Dict[str, np.ndarray],
                                 module_boundaries: List[Tuple[int, int]] = None) -> Dict[str, Any]:
        """分析注意力模式"""
        patterns = {}
        
        for layer_name, attention_matrix in attention_matrices.items():
            # 计算各种指标
            entropy = self.compute_attention_entropy(attention_matrix)
            concentration = self.compute_attention_concentration(attention_matrix)
            
            module_mass = 0.0
            if module_boundaries:
                module_mass = self.compute_module_attention_mass(attention_matrix, module_boundaries)
            
            patterns[layer_name] = {
                'entropy': entropy,
                'concentration': concentration,
                'module_mass': module_mass,
                'shape': attention_matrix.shape
            }
        
        return patterns
    
    def visualize_attention(self, attention_matrix: np.ndarray, tokens: List[str],
                          layer_name: str, head_idx: int = 0, 
                          output_path: str = None):
        """可视化注意力矩阵"""
        # 选择特定头的注意力
        if head_idx >= attention_matrix.shape[0]:
            head_idx = 0
        
        attention_head = attention_matrix[head_idx]
        
        # 创建热力图
        plt.figure(figsize=(12, 10))
        sns.heatmap(
            attention_head,
            xticklabels=tokens,
            yticklabels=tokens,
            cmap='Blues',
            cbar=True,
            square=True
        )
        
        plt.title(f'Attention Pattern - {layer_name} Head {head_idx}')
        plt.xlabel('Key Tokens')
        plt.ylabel('Query Tokens')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"📊 注意力可视化已保存: {output_path}")
        
        plt.show()
    
    def compare_architectures(self, explicit_attentions: List[Dict[str, np.ndarray]],
                           implicit_attentions: List[Dict[str, np.ndarray]],
                           output_dir: str):
        """比较显性和非显性架构的注意力模式"""
        ensure_dir(output_dir)
        
        # 计算平均注意力模式
        exp_patterns = self._compute_average_patterns(explicit_attentions)
        imp_patterns = self._compute_average_patterns(implicit_attentions)
        
        # 创建对比图
        self._create_comparison_plots(exp_patterns, imp_patterns, output_dir)
        
        # 统计检验
        self._statistical_comparison(exp_patterns, imp_patterns, output_dir)
        
        print(f"📊 注意力对比分析完成: {output_dir}")
    
    def _compute_average_patterns(self, attention_list: List[Dict[str, np.ndarray]]) -> Dict[str, Dict[str, float]]:
        """计算平均注意力模式"""
        if not attention_list:
            return {}
        
        # 收集所有层的指标
        layer_metrics = {}
        for attention_dict in attention_list:
            for layer_name, attention_matrix in attention_dict.items():
                if layer_name not in layer_metrics:
                    layer_metrics[layer_name] = {
                        'entropies': [],
                        'concentrations': [],
                        'module_masses': []
                    }
                
                patterns = self.analyze_attention_patterns({layer_name: attention_matrix})
                layer_metrics[layer_name]['entropies'].append(patterns[layer_name]['entropy'])
                layer_metrics[layer_name]['concentrations'].append(patterns[layer_name]['concentration'])
                layer_metrics[layer_name]['module_masses'].append(patterns[layer_name]['module_mass'])
        
        # 计算平均值
        avg_patterns = {}
        for layer_name, metrics in layer_metrics.items():
            avg_patterns[layer_name] = {
                'entropy_mean': np.mean(metrics['entropies']),
                'entropy_std': np.std(metrics['entropies']),
                'concentration_mean': np.mean(metrics['concentrations']),
                'concentration_std': np.std(metrics['concentrations']),
                'module_mass_mean': np.mean(metrics['module_masses']),
                'module_mass_std': np.std(metrics['module_masses'])
            }
        
        return avg_patterns
    
    def _create_comparison_plots(self, exp_patterns: Dict[str, Dict[str, float]],
                                imp_patterns: Dict[str, Dict[str, float]],
                                output_dir: str):
        """创建对比图"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 提取层数
        layers = list(exp_patterns.keys())
        layer_indices = [int(layer.split('_')[1]) for layer in layers]
        
        # 创建对比图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 注意力熵对比
        exp_entropies = [exp_patterns[layer]['entropy_mean'] for layer in layers]
        imp_entropies = [imp_patterns[layer]['entropy_mean'] for layer in layers]
        
        axes[0, 0].plot(layer_indices, exp_entropies, 'o-', label='显性架构', color='blue')
        axes[0, 0].plot(layer_indices, imp_entropies, 's-', label='非显性架构', color='red')
        axes[0, 0].set_xlabel('层数')
        axes[0, 0].set_ylabel('平均注意力熵')
        axes[0, 0].set_title('注意力熵对比')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 注意力集中度对比
        exp_concentrations = [exp_patterns[layer]['concentration_mean'] for layer in layers]
        imp_concentrations = [imp_patterns[layer]['concentration_mean'] for layer in layers]
        
        axes[0, 1].plot(layer_indices, exp_concentrations, 'o-', label='显性架构', color='blue')
        axes[0, 1].plot(layer_indices, imp_concentrations, 's-', label='非显性架构', color='red')
        axes[0, 1].set_xlabel('层数')
        axes[0, 1].set_ylabel('平均注意力集中度')
        axes[0, 1].set_title('注意力集中度对比')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 模块内注意力质量对比
        exp_module_masses = [exp_patterns[layer]['module_mass_mean'] for layer in layers]
        imp_module_masses = [imp_patterns[layer]['module_mass_mean'] for layer in layers]
        
        axes[1, 0].plot(layer_indices, exp_module_masses, 'o-', label='显性架构', color='blue')
        axes[1, 0].plot(layer_indices, imp_module_masses, 's-', label='非显性架构', color='red')
        axes[1, 0].set_xlabel('层数')
        axes[1, 0].set_ylabel('平均模块内注意力质量')
        axes[1, 0].set_title('模块内注意力质量对比')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 综合对比
        x = np.arange(len(layers))
        width = 0.35
        
        axes[1, 1].bar(x - width/2, exp_entropies, width, label='显性架构熵', alpha=0.7)
        axes[1, 1].bar(x + width/2, imp_entropies, width, label='非显性架构熵', alpha=0.7)
        axes[1, 1].set_xlabel('层数')
        axes[1, 1].set_ylabel('注意力熵')
        axes[1, 1].set_title('各层注意力熵对比')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(layer_indices)
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        comparison_path = os.path.join(output_dir, "attention_comparison.png")
        plt.savefig(comparison_path, dpi=300, bbox_inches='tight')
        print(f"📈 注意力对比图已保存: {comparison_path}")
        plt.show()
    
    def _statistical_comparison(self, exp_patterns: Dict[str, Dict[str, float]],
                              imp_patterns: Dict[str, Dict[str, float]],
                              output_dir: str):
        """统计比较"""
        from scipy.stats import ttest_ind, mannwhitneyu
        
        # 收集数据
        exp_entropies = [exp_patterns[layer]['entropy_mean'] for layer in exp_patterns.keys()]
        imp_entropies = [imp_patterns[layer]['entropy_mean'] for layer in imp_patterns.keys()]
        
        exp_concentrations = [exp_patterns[layer]['concentration_mean'] for layer in exp_patterns.keys()]
        imp_concentrations = [imp_patterns[layer]['concentration_mean'] for layer in imp_patterns.keys()]
        
        # 统计检验
        t_stat_entropy, t_p_entropy = ttest_ind(exp_entropies, imp_entropies)
        u_stat_entropy, u_p_entropy = mannwhitneyu(exp_entropies, imp_entropies, alternative='two-sided')
        
        t_stat_conc, t_p_conc = ttest_ind(exp_concentrations, imp_concentrations)
        u_stat_conc, u_p_conc = mannwhitneyu(exp_concentrations, imp_concentrations, alternative='two-sided')
        
        # 保存统计结果
        stats_results = {
            'entropy_comparison': {
                't_statistic': t_stat_entropy,
                't_p_value': t_p_entropy,
                'u_statistic': u_stat_entropy,
                'u_p_value': u_p_entropy,
                'explicit_mean': np.mean(exp_entropies),
                'implicit_mean': np.mean(imp_entropies)
            },
            'concentration_comparison': {
                't_statistic': t_stat_conc,
                't_p_value': t_p_conc,
                'u_statistic': u_stat_conc,
                'u_p_value': u_p_conc,
                'explicit_mean': np.mean(exp_concentrations),
                'implicit_mean': np.mean(imp_concentrations)
            }
        }
        
        stats_path = os.path.join(output_dir, "attention_statistics.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats_results, f, indent=2, ensure_ascii=False)
        
        print(f"📊 统计检验结果已保存: {stats_path}")
        print(f"   注意力熵 t检验: t={t_stat_entropy:.4f}, p={t_p_entropy:.4f}")
        print(f"   注意力集中度 t检验: t={t_stat_conc:.4f}, p={t_p_conc:.4f}")


def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="注意力机制分析")
    parser.add_argument("--model_dir", type=str, required=True,
                       help="模型目录")
    parser.add_argument("--test_file", type=str, required=True,
                       help="测试数据文件")
    parser.add_argument("--output_dir", type=str, default="./attention_analysis",
                       help="输出目录")
    parser.add_argument("--max_length", type=int, default=512,
                       help="最大序列长度")
    parser.add_argument("--device", type=str, default="auto",
                       help="设备类型")
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = AttentionAnalyzer(args.model_dir, args.device)
    
    # 加载模型
    analyzer.load_model()
    
    # 加载测试数据
    test_data = []
    with open(args.test_file, 'r', encoding='utf-8') as f:
        for line in f:
            test_data.append(json.loads(line.strip()))
    
    print(f"📊 分析 {len(test_data)} 个测试样本")
    
    # 提取注意力
    explicit_attentions = []
    implicit_attentions = []
    
    for sample in tqdm(test_data, desc="提取注意力"):
        text = sample.get('input', '')
        view = sample.get('view', '')
        
        try:
            attention_matrices = analyzer.extract_attention(text, args.max_length)
            
            if view == 'explicit':
                explicit_attentions.append(attention_matrices)
            elif view == 'non_explicit':
                implicit_attentions.append(attention_matrices)
        except Exception as e:
            print(f"⚠️ 处理样本失败: {e}")
            continue
    
    print(f"   显性架构样本: {len(explicit_attentions)}")
    print(f"   非显性架构样本: {len(implicit_attentions)}")
    
    # 比较分析
    if explicit_attentions and implicit_attentions:
        analyzer.compare_architectures(explicit_attentions, implicit_attentions, args.output_dir)
    
    print("✅ 注意力分析完成!")


if __name__ == "__main__":
    main()
