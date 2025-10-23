#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_trainer.py
----------------------------------------------------
线性探针训练工具

功能：
1. 提取模型中间层表征
2. 训练线性探针分类器
3. 分析表征的可分性
4. 比较显性和非显性架构的表征差异

依赖：
    pip install transformers torch scikit-learn matplotlib seaborn
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
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from scipy.stats import ttest_ind, mannwhitneyu


class ProbeTrainer:
    """线性探针训练器"""
    
    def __init__(self, model_path: str, device: str = "auto"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.tokenizer = None
        self.scaler = StandardScaler()
        
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
        
        # 加载模型（启用隐藏状态输出）
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=self.device,
            output_hidden_states=True
        )
        
        print(f"✅ 模型加载完成")
        print(f"   层数: {self.model.config.n_layer}")
        print(f"   隐藏维度: {self.model.config.n_embd}")
    
    def extract_representations(self, text: str, layer_idx: int = -1, 
                              max_length: int = 512) -> np.ndarray:
        """提取指定层的表征"""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        ).to(self.model.device)
        
        # 前向传播
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
        
        # 提取指定层的隐藏状态
        hidden_states = outputs.hidden_states[layer_idx]  # (batch, seq, hidden)
        
        # 转换为numpy数组
        representations = hidden_states[0].cpu().numpy()  # (seq, hidden)
        
        return representations
    
    def extract_token_representations(self, text: str, layer_idx: int = -1,
                                    max_length: int = 512) -> Tuple[np.ndarray, List[str]]:
        """提取token级别的表征"""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        ).to(self.model.device)
        
        # 前向传播
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
        
        # 提取指定层的隐藏状态
        hidden_states = outputs.hidden_states[layer_idx]  # (batch, seq, hidden)
        
        # 转换为numpy数组
        representations = hidden_states[0].cpu().numpy()  # (seq, hidden)
        
        # 获取tokens
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        return representations, tokens
    
    def create_architecture_labels(self, data: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """创建架构标签"""
        X = []
        y = []
        texts = []
        
        for sample in data:
            text = sample.get('input', '')
            view = sample.get('view', '')
            
            if not text or not view:
                continue
            
            # 提取表征
            try:
                representations = self.extract_representations(text)
                # 使用平均池化
                avg_representation = np.mean(representations, axis=0)
                
                X.append(avg_representation)
                y.append(1 if view == 'explicit' else 0)
                texts.append(text)
            except Exception as e:
                print(f"⚠️ 处理样本失败: {e}")
                continue
        
        return np.array(X), np.array(y), texts
    
    def create_semantic_labels(self, data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """创建语义标签（基于耦合度）"""
        X = []
        y_coupling = []
        y_architecture = []
        texts = []
        
        for sample in data:
            text = sample.get('input', '')
            view = sample.get('view', '')
            coupling = sample.get('coupling', {})
            
            if not text or not view:
                continue
            
            # 提取表征
            try:
                representations = self.extract_representations(text)
                avg_representation = np.mean(representations, axis=0)
                
                X.append(avg_representation)
                y_coupling.append(coupling.get('coupling_score', 0))
                y_architecture.append(1 if view == 'explicit' else 0)
                texts.append(text)
            except Exception as e:
                print(f"⚠️ 处理样本失败: {e}")
                continue
        
        return np.array(X), np.array(y_coupling), np.array(y_architecture), texts
    
    def train_architecture_probe(self, X: np.ndarray, y: np.ndarray, 
                              test_size: float = 0.2) -> Dict[str, Any]:
        """训练架构分类探针"""
        print("🔧 训练架构分类探针...")
        
        # 划分训练测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # 标准化特征
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练多种分类器
        classifiers = {
            'logistic_regression': LogisticRegression(max_iter=1000, random_state=42),
            'svm': SVC(kernel='rbf', random_state=42),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42)
        }
        
        results = {}
        for name, clf in classifiers.items():
            print(f"   训练 {name}...")
            
            # 训练
            clf.fit(X_train_scaled, y_train)
            
            # 预测
            y_pred = clf.predict(X_test_scaled)
            y_pred_proba = clf.predict_proba(X_test_scaled)[:, 1] if hasattr(clf, 'predict_proba') else None
            
            # 计算指标
            accuracy = accuracy_score(y_test, y_pred)
            
            # 交叉验证
            cv_scores = cross_val_score(clf, X_train_scaled, y_train, cv=5)
            
            results[name] = {
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'predictions': y_pred,
                'probabilities': y_pred_proba,
                'classifier': clf
            }
            
            print(f"     准确率: {accuracy:.4f}")
            print(f"     交叉验证: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        # 选择最佳分类器
        best_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
        best_results = results[best_name]
        
        print(f"✅ 最佳分类器: {best_name} (准确率: {best_results['accuracy']:.4f})")
        
        return {
            'results': results,
            'best_classifier': best_name,
            'best_results': best_results,
            'X_test': X_test,
            'y_test': y_test,
            'X_test_scaled': X_test_scaled
        }
    
    def train_coupling_probe(self, X: np.ndarray, y_coupling: np.ndarray,
                           test_size: float = 0.2) -> Dict[str, Any]:
        """训练耦合度回归探针"""
        print("🔧 训练耦合度回归探针...")
        
        # 划分训练测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_coupling, test_size=test_size, random_state=42
        )
        
        # 标准化特征
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练回归器
        regressor = LinearRegression()
        regressor.fit(X_train_scaled, y_train)
        
        # 预测
        y_pred = regressor.predict(X_test_scaled)
        
        # 计算指标
        from sklearn.metrics import mean_squared_error, r2_score
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"   均方误差: {mse:.4f}")
        print(f"   R²分数: {r2:.4f}")
        
        return {
            'regressor': regressor,
            'mse': mse,
            'r2': r2,
            'predictions': y_pred,
            'y_test': y_test,
            'X_test_scaled': X_test_scaled
        }
    
    def analyze_layer_representations(self, data: List[Dict[str, Any]], 
                                   output_dir: str):
        """分析不同层的表征质量"""
        print("🔍 分析不同层的表征质量...")
        
        # 为每个层训练探针
        layer_results = {}
        
        for layer_idx in range(self.model.config.n_layer):
            print(f"   分析层 {layer_idx}...")
            
            # 提取该层的表征
            X = []
            y = []
            
            for sample in data:
                text = sample.get('input', '')
                view = sample.get('view', '')
                
                if not text or not view:
                    continue
                
                try:
                    representations = self.extract_representations(text, layer_idx)
                    avg_representation = np.mean(representations, axis=0)
                    
                    X.append(avg_representation)
                    y.append(1 if view == 'explicit' else 0)
                except Exception as e:
                    continue
            
            if len(X) < 10:  # 样本太少
                continue
            
            X = np.array(X)
            y = np.array(y)
            
            # 训练探针
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # 标准化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # 训练分类器
            clf = LogisticRegression(max_iter=1000, random_state=42)
            clf.fit(X_train_scaled, y_train)
            
            # 评估
            accuracy = clf.score(X_test_scaled, y_test)
            cv_scores = cross_val_score(clf, X_train_scaled, y_train, cv=5)
            
            layer_results[layer_idx] = {
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
        
        # 可视化结果
        self._visualize_layer_analysis(layer_results, output_dir)
        
        return layer_results
    
    def _visualize_layer_analysis(self, layer_results: Dict[int, Dict[str, float]], 
                                output_dir: str):
        """可视化层分析结果"""
        ensure_dir(output_dir)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建图表
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # 提取数据
        layers = list(layer_results.keys())
        accuracies = [layer_results[layer]['accuracy'] for layer in layers]
        cv_means = [layer_results[layer]['cv_mean'] for layer in layers]
        cv_stds = [layer_results[layer]['cv_std'] for layer in layers]
        
        # 1. 准确率随层数变化
        axes[0].plot(layers, accuracies, 'o-', color='blue', linewidth=2, markersize=6)
        axes[0].set_xlabel('层数')
        axes[0].set_ylabel('测试准确率')
        axes[0].set_title('各层表征分类准确率')
        axes[0].grid(True, alpha=0.3)
        axes[0].set_ylim(0, 1)
        
        # 2. 交叉验证结果
        axes[1].errorbar(layers, cv_means, yerr=cv_stds, fmt='o-', 
                        color='red', linewidth=2, markersize=6, capsize=5)
        axes[1].set_xlabel('层数')
        axes[1].set_ylabel('交叉验证准确率')
        axes[1].set_title('各层表征交叉验证结果')
        axes[1].grid(True, alpha=0.3)
        axes[1].set_ylim(0, 1)
        
        plt.tight_layout()
        
        # 保存图表
        layer_analysis_path = os.path.join(output_dir, "layer_analysis.png")
        plt.savefig(layer_analysis_path, dpi=300, bbox_inches='tight')
        print(f"📊 层分析图表已保存: {layer_analysis_path}")
        plt.show()
    
    def compare_architectures(self, explicit_data: List[Dict[str, Any]],
                           implicit_data: List[Dict[str, Any]],
                           output_dir: str):
        """比较显性和非显性架构的表征差异"""
        print("🔍 比较架构表征差异...")
        
        # 提取表征
        exp_X, exp_y, exp_texts = self.create_architecture_labels(explicit_data)
        imp_X, imp_y, imp_texts = self.create_architecture_labels(implicit_data)
        
        print(f"   显性架构样本: {len(exp_X)}")
        print(f"   非显性架构样本: {len(imp_X)}")
        
        # 训练探针
        exp_results = self.train_architecture_probe(exp_X, exp_y)
        imp_results = self.train_architecture_probe(imp_X, imp_y)
        
        # 比较结果
        self._create_comparison_plots(exp_results, imp_results, output_dir)
        
        # 统计检验
        self._statistical_comparison(exp_results, imp_results, output_dir)
        
        print(f"📊 架构表征比较完成: {output_dir}")
    
    def _create_comparison_plots(self, exp_results: Dict[str, Any],
                                imp_results: Dict[str, Any],
                                output_dir: str):
        """创建比较图"""
        ensure_dir(output_dir)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 准确率对比
        classifiers = list(exp_results['results'].keys())
        exp_accuracies = [exp_results['results'][name]['accuracy'] for name in classifiers]
        imp_accuracies = [imp_results['results'][name]['accuracy'] for name in classifiers]
        
        x = np.arange(len(classifiers))
        width = 0.35
        
        axes[0, 0].bar(x - width/2, exp_accuracies, width, label='显性架构', alpha=0.7)
        axes[0, 0].bar(x + width/2, imp_accuracies, width, label='非显性架构', alpha=0.7)
        axes[0, 0].set_xlabel('分类器')
        axes[0, 0].set_ylabel('准确率')
        axes[0, 0].set_title('分类器准确率对比')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(classifiers, rotation=45)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 交叉验证对比
        exp_cv_means = [exp_results['results'][name]['cv_mean'] for name in classifiers]
        imp_cv_means = [imp_results['results'][name]['cv_mean'] for name in classifiers]
        exp_cv_stds = [exp_results['results'][name]['cv_std'] for name in classifiers]
        imp_cv_stds = [imp_results['results'][name]['cv_std'] for name in classifiers]
        
        axes[0, 1].errorbar(x, exp_cv_means, yerr=exp_cv_stds, fmt='o-', 
                           label='显性架构', capsize=5)
        axes[0, 1].errorbar(x, imp_cv_means, yerr=imp_cv_stds, fmt='s-', 
                           label='非显性架构', capsize=5)
        axes[0, 1].set_xlabel('分类器')
        axes[0, 1].set_ylabel('交叉验证准确率')
        axes[0, 1].set_title('交叉验证结果对比')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(classifiers, rotation=45)
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 混淆矩阵（最佳分类器）
        exp_best = exp_results['best_results']
        imp_best = imp_results['best_results']
        
        exp_cm = confusion_matrix(exp_results['y_test'], exp_best['predictions'])
        imp_cm = confusion_matrix(imp_results['y_test'], imp_best['predictions'])
        
        sns.heatmap(exp_cm, annot=True, fmt='d', cmap='Blues', ax=axes[1, 0])
        axes[1, 0].set_title('显性架构混淆矩阵')
        axes[1, 0].set_xlabel('预测标签')
        axes[1, 0].set_ylabel('真实标签')
        
        sns.heatmap(imp_cm, annot=True, fmt='d', cmap='Reds', ax=axes[1, 1])
        axes[1, 1].set_title('非显性架构混淆矩阵')
        axes[1, 1].set_xlabel('预测标签')
        axes[1, 1].set_ylabel('真实标签')
        
        plt.tight_layout()
        
        # 保存图表
        comparison_path = os.path.join(output_dir, "probe_comparison.png")
        plt.savefig(comparison_path, dpi=300, bbox_inches='tight')
        print(f"📊 探针比较图已保存: {comparison_path}")
        plt.show()
    
    def _statistical_comparison(self, exp_results: Dict[str, Any],
                              imp_results: Dict[str, Any],
                              output_dir: str):
        """统计比较"""
        # 收集准确率数据
        exp_accuracies = [exp_results['results'][name]['accuracy'] for name in exp_results['results'].keys()]
        imp_accuracies = [imp_results['results'][name]['accuracy'] for name in imp_results['results'].keys()]
        
        # 统计检验
        t_stat, t_p = ttest_ind(exp_accuracies, imp_accuracies)
        u_stat, u_p = mannwhitneyu(exp_accuracies, imp_accuracies, alternative='two-sided')
        
        # 保存统计结果
        stats_results = {
            'accuracy_comparison': {
                't_statistic': t_stat,
                't_p_value': t_p,
                'u_statistic': u_stat,
                'u_p_value': u_p,
                'explicit_mean': np.mean(exp_accuracies),
                'implicit_mean': np.mean(imp_accuracies),
                'explicit_std': np.std(exp_accuracies),
                'implicit_std': np.std(imp_accuracies)
            }
        }
        
        stats_path = os.path.join(output_dir, "probe_statistics.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats_results, f, indent=2, ensure_ascii=False)
        
        print(f"📊 统计检验结果已保存: {stats_path}")
        print(f"   准确率 t检验: t={t_stat:.4f}, p={t_p:.4f}")
        print(f"   显性架构平均准确率: {np.mean(exp_accuracies):.4f} ± {np.std(exp_accuracies):.4f}")
        print(f"   非显性架构平均准确率: {np.mean(imp_accuracies):.4f} ± {np.std(imp_accuracies):.4f}")


def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="线性探针训练")
    parser.add_argument("--model_dir", type=str, required=True,
                       help="模型目录")
    parser.add_argument("--explicit_data", type=str, required=True,
                       help="显性架构数据文件")
    parser.add_argument("--implicit_data", type=str, required=True,
                       help="非显性架构数据文件")
    parser.add_argument("--output_dir", type=str, default="./probe_analysis",
                       help="输出目录")
    parser.add_argument("--device", type=str, default="auto",
                       help="设备类型")
    
    args = parser.parse_args()
    
    # 创建探针训练器
    trainer = ProbeTrainer(args.model_dir, args.device)
    
    # 加载模型
    trainer.load_model()
    
    # 加载数据
    explicit_data = []
    with open(args.explicit_data, 'r', encoding='utf-8') as f:
        for line in f:
            explicit_data.append(json.loads(line.strip()))
    
    implicit_data = []
    with open(args.implicit_data, 'r', encoding='utf-8') as f:
        for line in f:
            implicit_data.append(json.loads(line.strip()))
    
    print(f"📊 加载数据:")
    print(f"   显性架构样本: {len(explicit_data)}")
    print(f"   非显性架构样本: {len(implicit_data)}")
    
    # 比较架构
    trainer.compare_architectures(explicit_data, implicit_data, args.output_dir)
    
    # 分析层表征
    all_data = explicit_data + implicit_data
    layer_results = trainer.analyze_layer_representations(all_data, args.output_dir)
    
    print("✅ 探针训练完成!")


if __name__ == "__main__":
    main()
