#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_pipeline.py
----------------------------------------------------
显性架构实验评估管道

功能：
1. 加载微调后的模型
2. 对测试集进行推理
3. 计算多种评估指标
4. 生成详细的评估报告

依赖：
    pip install transformers datasets torch evaluate
----------------------------------------------------
"""

import os
import json
import torch
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
from tqdm import tqdm
import argparse

from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    pipeline
)
from datasets import load_dataset
import evaluate


class CodeCompletionEvaluator:
    """代码补全评估器"""
    
    def __init__(self, model_path: str, device: str = "auto"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.tokenizer = None
        self.metrics = {}
        
        # 加载评估指标
        self._load_metrics()
        
    def _load_metrics(self):
        """加载评估指标"""
        try:
            self.bleu_metric = evaluate.load("bleu")
            self.rouge_metric = evaluate.load("rouge")
            self.meteor_metric = evaluate.load("meteor")
        except Exception as e:
            print(f"⚠️ 部分评估指标加载失败: {e}")
            self.bleu_metric = None
            self.rouge_metric = None
            self.meteor_metric = None
    
    def load_model(self):
        """加载模型和tokenizer"""
        print(f"🔧 加载模型: {self.model_path}")
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            use_fast=True
        )
        
        # 设置pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=self.device
        )
        
        print(f"✅ 模型加载完成")
        print(f"   设备: {next(self.model.parameters()).device}")
        print(f"   数据类型: {next(self.model.parameters()).dtype}")
    
    def generate_completion(self, input_text: str, max_new_tokens: int = 256, 
                          temperature: float = 0.7, do_sample: bool = False) -> str:
        """生成代码补全"""
        # 检查输入文本是否有效
        if not input_text or len(input_text.strip()) == 0:
            return ""
        
        # Tokenize输入
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
            padding=True
        ).to(self.model.device)
        
        # 检查tokenized输入是否有效
        if inputs['input_ids'].shape[1] == 0:
            return ""
        
        # Generate
        with torch.no_grad():
            try:
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    top_p=0.9,
                    top_k=50,
                    no_repeat_ngram_size=2
                )
            except RuntimeError as e:
                if "probability tensor contains" in str(e):
                    # 如果概率分布有问题，使用贪婪解码
                    print(f"⚠️ 概率分布异常，使用贪婪解码: {e}")
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,  # 贪婪解码
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        repetition_penalty=1.1
                    )
                else:
                    raise e
        
        # 解码输出
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return generated_text.strip()
    
    def exact_match(self, prediction: str, reference: str) -> bool:
        """计算精确匹配"""
        return prediction.strip() == reference.strip()
    
    def code_bleu_score(self, prediction: str, reference: str) -> float:
        """计算CodeBLEU分数"""
        try:
            # 简单的BLEU计算（实际应用中可以使用更复杂的CodeBLEU）
            if self.bleu_metric is not None:
                result = self.bleu_metric.compute(
                    predictions=[prediction],
                    references=[[reference]]
                )
                return result['bleu']
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def rouge_score(self, prediction: str, reference: str) -> Dict[str, float]:
        """计算ROUGE分数"""
        try:
            if self.rouge_metric is not None:
                result = self.rouge_metric.compute(
                    predictions=[prediction],
                    references=[reference]
                )
                return {
                    'rouge1': result['rouge1'],
                    'rouge2': result['rouge2'],
                    'rougeL': result['rougeL']
                }
            else:
                return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}
        except Exception:
            return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}
    
    def meteor_score(self, prediction: str, reference: str) -> float:
        """计算METEOR分数"""
        try:
            if self.meteor_metric is not None:
                result = self.meteor_metric.compute(
                    predictions=[prediction],
                    references=[reference]
                )
                return result['meteor']
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def evaluate_single_sample(self, sample: Dict[str, Any], 
                              max_new_tokens: int = 256) -> Dict[str, Any]:
        """评估单个样本"""
        # 兼容不同的数据格式
        input_text = sample.get('input', sample.get('prefix', ''))
        reference = sample.get('target', sample.get('suffix', ''))
        
        # 调试信息
        if not input_text or len(input_text.strip()) == 0:
            print(f"⚠️ 警告: 输入文本为空，跳过样本")
            return {
                'exact_match': False,
                'bleu_score': 0.0,
                'rouge_scores': {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0},
                'meteor_score': 0.0,
                'prediction': '',
                'reference': reference
            }
        
        # 生成预测
        prediction = self.generate_completion(input_text, max_new_tokens)
        
        # 计算各种指标
        exact_match = self.exact_match(prediction, reference)
        bleu_score = self.code_bleu_score(prediction, reference)
        rouge_scores = self.rouge_score(prediction, reference)
        meteor_score = self.meteor_score(prediction, reference)
        
        return {
            'input': input_text,
            'reference': reference,
            'prediction': prediction,
            'exact_match': exact_match,
            'bleu': bleu_score,
            'rouge1': rouge_scores['rouge1'],
            'rouge2': rouge_scores['rouge2'],
            'rougeL': rouge_scores['rougeL'],
            'meteor': meteor_score,
            'view': sample.get('view', 'unknown'),
            'coupling': sample.get('coupling', {})
        }
    
    def evaluate_dataset(self, test_file: str, output_file: str = None, 
                        max_new_tokens: int = 256) -> Dict[str, Any]:
        """评估整个数据集"""
        print(f"📊 评估数据集: {test_file}")
        
        # 加载测试数据
        if test_file.endswith('.jsonl'):
            test_data = []
            with open(test_file, 'r', encoding='utf-8') as f:
                for line in f:
                    test_data.append(json.loads(line.strip()))
        elif test_file.endswith('.json'):
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
        else:
            raise ValueError("不支持的文件格式")
        
        print(f"   测试样本数: {len(test_data)}")
        
        # 评估每个样本
        results = []
        for sample in tqdm(test_data, desc="评估样本"):
            result = self.evaluate_single_sample(sample, max_new_tokens)
            results.append(result)
        
        # 计算总体指标
        overall_metrics = self._compute_overall_metrics(results)
        
        # 按架构类型分析
        architecture_analysis = self._analyze_by_architecture(results)
        
        # 按耦合度分析
        coupling_analysis = self._analyze_by_coupling(results)
        
        # 保存结果
        if output_file:
            self._save_results(results, overall_metrics, architecture_analysis, 
                              coupling_analysis, output_file)
        
        return {
            'results': results,
            'overall_metrics': overall_metrics,
            'architecture_analysis': architecture_analysis,
            'coupling_analysis': coupling_analysis
        }
    
    def _compute_overall_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算总体指标"""
        if not results:
            return {}
        
        # 基本指标
        exact_matches = [r['exact_match'] for r in results]
        bleu_scores = [r['bleu'] for r in results]
        rouge1_scores = [r['rouge1'] for r in results]
        rouge2_scores = [r['rouge2'] for r in results]
        rougeL_scores = [r['rougeL'] for r in results]
        meteor_scores = [r['meteor'] for r in results]
        
        return {
            'exact_match_rate': np.mean(exact_matches),
            'bleu_mean': np.mean(bleu_scores),
            'bleu_std': np.std(bleu_scores),
            'rouge1_mean': np.mean(rouge1_scores),
            'rouge1_std': np.std(rouge1_scores),
            'rouge2_mean': np.mean(rouge2_scores),
            'rouge2_std': np.std(rouge2_scores),
            'rougeL_mean': np.mean(rougeL_scores),
            'rougeL_std': np.std(rougeL_scores),
            'meteor_mean': np.mean(meteor_scores),
            'meteor_std': np.std(meteor_scores),
            'total_samples': len(results)
        }
    
    def _analyze_by_architecture(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按架构类型分析结果"""
        explicit_results = [r for r in results if r.get('view') == 'explicit']
        non_explicit_results = [r for r in results if r.get('view') == 'non_explicit']
        
        analysis = {}
        
        if explicit_results:
            analysis['explicit'] = self._compute_overall_metrics(explicit_results)
        
        if non_explicit_results:
            analysis['non_explicit'] = self._compute_overall_metrics(non_explicit_results)
        
        # 比较两种架构
        if explicit_results and non_explicit_results:
            exp_em = np.mean([r['exact_match'] for r in explicit_results])
            non_exp_em = np.mean([r['exact_match'] for r in non_explicit_results])
            
            analysis['comparison'] = {
                'exact_match_difference': exp_em - non_exp_em,
                'explicit_samples': len(explicit_results),
                'non_explicit_samples': len(non_explicit_results)
            }
        
        return analysis
    
    def _analyze_by_coupling(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按耦合度分析结果"""
        # 按耦合度分组
        low_coupling = []
        medium_coupling = []
        high_coupling = []
        
        for result in results:
            coupling = result.get('coupling', {})
            coupling_score = coupling.get('coupling_score', 0)
            
            if coupling_score < 5:
                low_coupling.append(result)
            elif coupling_score < 15:
                medium_coupling.append(result)
            else:
                high_coupling.append(result)
        
        analysis = {}
        
        if low_coupling:
            analysis['low_coupling'] = self._compute_overall_metrics(low_coupling)
            analysis['low_coupling']['sample_count'] = len(low_coupling)
        
        if medium_coupling:
            analysis['medium_coupling'] = self._compute_overall_metrics(medium_coupling)
            analysis['medium_coupling']['sample_count'] = len(medium_coupling)
        
        if high_coupling:
            analysis['high_coupling'] = self._compute_overall_metrics(high_coupling)
            analysis['high_coupling']['sample_count'] = len(high_coupling)
        
        return analysis
    
    def _save_results(self, results: List[Dict[str, Any]], overall_metrics: Dict[str, float],
                     architecture_analysis: Dict[str, Any], coupling_analysis: Dict[str, Any],
                     output_file: str):
        """保存评估结果"""
        output_data = {
            'overall_metrics': overall_metrics,
            'architecture_analysis': architecture_analysis,
            'coupling_analysis': coupling_analysis,
            'detailed_results': results
        }
        
        # 保存JSON结果
        json_file = output_file.replace('.jsonl', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # 保存详细结果
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"📊 评估结果已保存:")
        print(f"   详细结果: {output_file}")
        print(f"   汇总结果: {json_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="显性架构实验评估")
    parser.add_argument("--model_dir", type=str, required=True,
                       help="微调后的模型目录")
    parser.add_argument("--test_file", type=str, required=True,
                       help="测试数据文件")
    parser.add_argument("--output", type=str, default="./evaluation_results.jsonl",
                       help="输出文件")
    parser.add_argument("--max_new_tokens", type=int, default=256,
                       help="最大生成token数")
    parser.add_argument("--device", type=str, default="auto",
                       help="设备类型")
    
    args = parser.parse_args()
    
    # 创建评估器
    evaluator = CodeCompletionEvaluator(args.model_dir, args.device)
    
    # 加载模型
    evaluator.load_model()
    
    # 评估数据集
    results = evaluator.evaluate_dataset(
        args.test_file, 
        args.output, 
        args.max_new_tokens
    )
    
    # 打印结果摘要
    print("\n📈 评估结果摘要:")
    print(f"   总样本数: {results['overall_metrics']['total_samples']}")
    print(f"   精确匹配率: {results['overall_metrics']['exact_match_rate']:.4f}")
    print(f"   BLEU分数: {results['overall_metrics']['bleu_mean']:.4f}")
    print(f"   ROUGE-L分数: {results['overall_metrics']['rougeL_mean']:.4f}")
    print(f"   METEOR分数: {results['overall_metrics']['meteor_mean']:.4f}")
    
    # 架构对比
    if 'comparison' in results['architecture_analysis']:
        comp = results['architecture_analysis']['comparison']
        print(f"\n🏗️ 架构对比:")
        print(f"   显性架构样本: {comp['explicit_samples']}")
        print(f"   非显性架构样本: {comp['non_explicit_samples']}")
        print(f"   精确匹配差异: {comp['exact_match_difference']:.4f}")
    
    print("✅ 评估完成!")


if __name__ == "__main__":
    main()
