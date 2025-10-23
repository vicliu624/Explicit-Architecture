#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finetune.py
----------------------------------------------------
显性架构实验模型微调脚本

功能：
1. 加载预训练模型和tokenizer
2. 准备训练数据（显性/非显性架构样本）
3. 微调模型用于函数补全任务
4. 支持多种模型架构和训练策略

依赖：
    pip install transformers datasets torch accelerate
----------------------------------------------------
"""

import os
import json
import math
import random
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoConfig, AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling,
    set_seed, EarlyStoppingCallback
)
from datasets import load_dataset, Dataset as HFDataset
from tqdm import tqdm


@dataclass
class ModelConfig:
    """模型配置"""
    model_name_or_path: str = "gpt2"
    output_dir: str = "./outputs/finetune"
    train_file: str = "./data/tasks/train.jsonl"
    validation_file: str = "./data/tasks/val.jsonl"
    test_file: str = "./data/tasks/test.jsonl"
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    num_train_epochs: int = 3
    seed: int = 42
    max_length: int = 1024
    mask_token: str = "[MASKED_FUNCTION_BODY]"
    padding_side: str = "right"
    warmup_steps: int = 100
    logging_steps: int = 50
    save_steps: int = 500
    eval_steps: int = 500
    early_stopping_patience: int = 3
    fp16: bool = True
    dataloader_num_workers: int = 4


class CodeCompletionDataset(Dataset):
    """代码补全数据集"""
    
    def __init__(self, data_path: str, tokenizer, max_length: int = 1024, mask_token: str = "[MASKED_FUNCTION_BODY]"):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.mask_token = mask_token
        
        # 加载数据
        self.data = self._load_data(data_path)
        print(f"📊 加载数据集: {len(self.data)} 个样本")
        
    def _load_data(self, data_path: str) -> List[Dict[str, Any]]:
        """加载数据文件"""
        data = []
        if data_path.endswith('.jsonl'):
            with open(data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data.append(json.loads(line.strip()))
        elif data_path.endswith('.json'):
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        return data
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # 获取输入和目标（兼容不同数据格式）
        input_text = item.get('input', item.get('prefix', ''))
        target_text = item.get('target', item.get('suffix', ''))
        
        # 验证数据
        if not input_text or not target_text:
            print(f"⚠️ 警告: 样本 {idx} 数据不完整，跳过")
            # 返回一个默认的有效样本
            input_text = "def hello():"
            target_text = "    print('Hello World')"
        
        # 创建完整的序列：输入 + 目标
        full_text = input_text + target_text
        
        # Tokenize完整序列（固定长度，便于批处理对齐）
        encoding = self.tokenizer(
            full_text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors="pt"
        )
        
        # 计算输入部分的长度（同样固定长度编码，仅用于获得输入长度）
        input_encoding = self.tokenizer(
            input_text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors="pt"
        )
        
        input_length = len(input_encoding['input_ids'][0])
        total_length = len(encoding['input_ids'][0])
        
        # 确保至少有一个目标token
        if input_length >= total_length:
            input_length = max(1, total_length - 1)
        
        # 创建标签：输入部分为-100，目标部分为实际token ids
        labels = [-100] * input_length + encoding['input_ids'][0][input_length:].tolist()
        
        # 确保labels和input_ids长度一致
        if len(labels) != total_length:
            if len(labels) < total_length:
                labels.extend([-100] * (total_length - len(labels)))
            else:
                labels = labels[:total_length]
        
        # 验证标签有效性（极端情况下再次保证至少1个有效标签）
        if all(l == -100 for l in labels):
            labels[-1] = int(encoding['input_ids'][0][-1].item())
        
        return {
            'input_ids': encoding['input_ids'][0],
            'attention_mask': encoding['attention_mask'][0],
            'labels': torch.tensor(labels, dtype=torch.long)
        }


class CodeCompletionTrainer:
    """代码补全训练器"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        # 设置随机种子
        set_seed(config.seed)
        
    def setup_model(self):
        """设置模型和tokenizer"""
        print(f"🔧 加载模型: {self.config.model_name_or_path}")
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            use_fast=True
        )
        
        # 添加特殊token
        if self.tokenizer.pad_token is None:
            self.tokenizer.add_special_tokens({"pad_token": "<|pad|>"})
        
        # 设置padding方向
        self.tokenizer.padding_side = self.config.padding_side
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32
        )
        
        # 调整token embedding大小
        self.model.resize_token_embeddings(len(self.tokenizer))
        
        print(f"✅ 模型加载完成")
        print(f"   词汇表大小: {len(self.tokenizer)}")
        print(f"   模型参数: {self.model.num_parameters():,}")
    
    def prepare_data(self):
        """准备训练数据"""
        print("📊 准备训练数据...")
        
        # 加载训练和验证数据
        train_dataset = CodeCompletionDataset(
            self.config.train_file,
            self.tokenizer,
            self.config.max_length,
            self.config.mask_token
        )
        
        val_dataset = CodeCompletionDataset(
            self.config.validation_file,
            self.tokenizer,
            self.config.max_length,
            self.config.mask_token
        )
        
        print(f"   训练集: {len(train_dataset)} 个样本")
        print(f"   验证集: {len(val_dataset)} 个样本")
        
        # 调试：打印第一个样本
        if len(train_dataset) > 0:
            sample = train_dataset[0]
            print(f"🔍 样本调试:")
            print(f"   input_ids shape: {sample['input_ids'].shape}")
            print(f"   labels shape: {sample['labels'].shape}")
            print(f"   labels中有-100的数量: {(sample['labels'] == -100).sum().item()}")
            print(f"   labels中有效token数量: {(sample['labels'] != -100).sum().item()}")
        
        return train_dataset, val_dataset
    
    def setup_trainer(self, train_dataset, val_dataset):
        """设置训练器"""
        print("🔧 设置训练器...")
        
        # 训练参数
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            num_train_epochs=self.config.num_train_epochs,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            warmup_steps=self.config.warmup_steps,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=self.config.fp16,
            dataloader_num_workers=self.config.dataloader_num_workers,
            seed=self.config.seed,
            report_to="none",  # 禁用wandb等
            remove_unused_columns=False,
        )
        
        # 数据整理器
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # 使用因果语言建模
            pad_to_multiple_of=8 if self.config.fp16 else None
        )
        
        # 早停回调
        early_stopping = EarlyStoppingCallback(
            early_stopping_patience=self.config.early_stopping_patience
        )
        
        # 创建训练器
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            callbacks=[early_stopping]
        )
        
        print("✅ 训练器设置完成")
    
    def train(self):
        """开始训练"""
        print("🚀 开始训练...")
        
        # 训练前评估
        print("📊 训练前评估...")
        eval_results = self.trainer.evaluate()
        eval_loss = eval_results.get('eval_loss', float('nan'))
        if not (isinstance(eval_loss, (int, float)) and not (eval_loss != eval_loss)):  # 检查是否为nan
            print(f"   初始验证损失: {eval_loss:.4f}")
        else:
            print(f"   初始验证损失: nan (数值不稳定)")
        
        # 开始训练
        train_results = self.trainer.train()
        
        # 训练后评估
        print("📊 训练后评估...")
        final_eval_results = self.trainer.evaluate()
        eval_loss = final_eval_results.get('eval_loss', float('nan'))
        if not (isinstance(eval_loss, (int, float)) and not (eval_loss != eval_loss)):  # 检查是否为nan
            print(f"   最终验证损失: {eval_loss:.4f}")
        else:
            print(f"   最终验证损失: nan (数值不稳定)")
        
        # 保存模型
        self.trainer.save_model()
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        print("✅ 训练完成!")
        print(f"   模型已保存至: {self.config.output_dir}")
        
        return train_results, final_eval_results
    
    def evaluate_model(self, test_file: str = None):
        """评估模型性能"""
        if test_file is None:
            test_file = self.config.test_file
        
        print(f"📊 评估模型性能: {test_file}")
        
        # 加载测试数据
        test_dataset = CodeCompletionDataset(
            test_file,
            self.tokenizer,
            self.config.max_length,
            self.config.mask_token
        )
        
        # 评估
        eval_results = self.trainer.evaluate(test_dataset)
        
        print("📈 测试结果:")
        for key, value in eval_results.items():
            print(f"   {key}: {value:.4f}")
        
        return eval_results


def load_config(config_path: str) -> ModelConfig:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = json.load(f)
    
    return ModelConfig(**config_dict)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="显性架构实验模型微调")
    parser.add_argument("--config", type=str, default="configs/finetune_config.json",
                       help="配置文件路径")
    parser.add_argument("--model_name", type=str, default="gpt2",
                       help="预训练模型名称")
    parser.add_argument("--output_dir", type=str, default="./outputs/finetune",
                       help="输出目录")
    parser.add_argument("--train_file", type=str, required=True,
                       help="训练数据文件")
    parser.add_argument("--val_file", type=str, required=True,
                       help="验证数据文件")
    parser.add_argument("--test_file", type=str, default=None,
                       help="测试数据文件")
    parser.add_argument("--epochs", type=int, default=3,
                       help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=4,
                       help="批次大小")
    parser.add_argument("--learning_rate", type=float, default=5e-5,
                       help="学习率")
    parser.add_argument("--max_length", type=int, default=1024,
                       help="最大序列长度")
    parser.add_argument("--seed", type=int, default=42,
                       help="随机种子")
    
    args = parser.parse_args()
    
    # 创建配置
    config = ModelConfig(
        model_name_or_path=args.model_name,
        output_dir=args.output_dir,
        train_file=args.train_file,
        validation_file=args.val_file,
        test_file=args.test_file,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
        seed=args.seed
    )
    
    # 创建训练器
    trainer = CodeCompletionTrainer(config)
    
    # 设置模型
    trainer.setup_model()
    
    # 准备数据
    train_dataset, val_dataset = trainer.prepare_data()
    
    # 设置训练器
    trainer.setup_trainer(train_dataset, val_dataset)
    
    # 开始训练
    train_results, eval_results = trainer.train()
    
    # 评估模型
    if args.test_file:
        test_results = trainer.evaluate_model(args.test_file)
    
    print("🎯 训练流程完成!")


if __name__ == "__main__":
    main()
