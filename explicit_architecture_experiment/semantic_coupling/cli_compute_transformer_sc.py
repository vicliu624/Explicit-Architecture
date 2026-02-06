"""
从 Transformer 内部机制直接计算语义耦合度。

新思路：不依赖 AST、调用图，直接从 Transformer 的 attention、embedding、perplexity 提取指标。
直接读取源代码工程，按文件/类划分模块。
"""

import argparse
import os
import re
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel, AutoModelForMaskedLM

from .transformer_metrics import (
    compute_perplexity_metrics,
    compute_layer_wise_semantic_coupling,
    compute_attention_coupling_matrix,
)
from .io import save_matrix_csv


def scan_source_files(
    source_root: str,
    file_extensions: List[str] = None,
    exclude_patterns: List[str] = None,
) -> List[Tuple[str, str]]:
    """
    扫描源代码工程，返回 (module_id, source_code) 列表。
    
    Parameters
    ----------
    source_root:
        源代码根目录
    file_extensions:
        文件扩展名列表（默认: ['.java', '.py', '.js', '.ts']）
    exclude_patterns:
        排除模式列表（如 ['test', '__pycache__']）
    
    Returns
    -------
    List[Tuple[str, str]]
        [(module_id, source_code), ...]
        module_id 通常是文件的相对路径或类名
    """
    if file_extensions is None:
        file_extensions = ['.java', '.py', '.js', '.ts', '.cpp', '.c', '.h', '.hpp']
    
    if exclude_patterns is None:
        exclude_patterns = ['test', '__pycache__', '.git', 'node_modules', 'target', 'build']
    
    source_root_path = Path(source_root).resolve()
    modules = []
    
    print(f"Scanning source files in: {source_root_path}")
    
    for ext in file_extensions:
        for file_path in source_root_path.rglob(f"*{ext}"):
            # 检查是否应该排除
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    should_exclude = True
                    break
            if should_exclude:
                continue
            
            try:
                # 读取文件内容
                source_code = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # 生成模块 ID（使用相对路径）
                try:
                    module_id = str(file_path.relative_to(source_root_path))
                except ValueError:
                    module_id = str(file_path)
                
                modules.append((module_id, source_code))
            except Exception as e:
                print(f"Warning: Failed to read {file_path}: {e}")
                continue
    
    print(f"Found {len(modules)} source files")
    return modules


def split_java_classes(source_code: str) -> List[Tuple[str, str]]:
    """
    将 Java 文件按类分割（简单实现，基于大括号匹配）。
    
    返回 [(class_name, class_code), ...]
    """
    import re
    
    classes = []
    lines = source_code.split('\n')
    
    current_class = None
    current_code = []
    brace_count = 0
    in_class = False
    
    for line in lines:
        # 检测类/接口/枚举定义
        class_match = re.search(r'\b(class|interface|enum)\s+(\w+)', line)
        if class_match:
            if in_class and current_class:
                classes.append((current_class, '\n'.join(current_code)))
            
            class_name = class_match.group(2)
            current_class = class_name
            current_code = [line]
            brace_count = line.count('{') - line.count('}')
            in_class = True
            continue
        
        if in_class:
            current_code.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                classes.append((current_class, '\n'.join(current_code)))
                current_class = None
                current_code = []
                in_class = False
    
    return classes if classes else [("File", source_code)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从 Transformer 内部机制计算语义耦合度（直接处理源代码工程）",
    )
    parser.add_argument(
        "--source-root",
        required=True,
        help="源代码根目录（如：/path/to/project/src/main/java）",
    )
    parser.add_argument(
        "--out-prefix",
        required=True,
        help="输出文件前缀",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="microsoft/codebert-base",
        help="Transformer 模型名称（默认: microsoft/codebert-base）",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="计算设备（默认: 自动选择）",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="模型缓存目录",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="批处理大小（默认: 8）",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="最大序列长度（默认: 512）",
    )
    parser.add_argument(
        "--layers",
        type=str,
        default=None,
        help="要提取的层索引，用逗号分隔（如 '0,1,2' 或 'low,mid,high'），默认所有层",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        default="all",
        help="要计算的指标：attention,embedding,perplexity,layer_wise,all（默认: all）",
    )
    parser.add_argument(
        "--file-extensions",
        type=str,
        default=".java",
        help="文件扩展名，用逗号分隔（默认: .java）",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default="test,__pycache__,.git,node_modules,target,build",
        help="排除模式，用逗号分隔（默认: test,__pycache__,.git,node_modules,target,build）",
    )
    parser.add_argument(
        "--split-classes",
        action="store_true",
        help="是否按类分割 Java 文件（默认: False，整个文件作为一个模块）",
    )

    args = parser.parse_args()

    # 扫描源代码文件
    file_extensions = [ext.strip() for ext in args.file_extensions.split(",")]
    exclude_patterns = [p.strip() for p in args.exclude.split(",")]
    
    file_modules = scan_source_files(
        args.source_root,
        file_extensions=file_extensions,
        exclude_patterns=exclude_patterns,
    )
    
    # 如果启用类分割，将 Java 文件按类分割
    if args.split_classes and '.java' in file_extensions:
        print("\nSplitting Java files by classes...")
        all_modules = []
        for module_id, source_code in file_modules:
            if module_id.endswith('.java'):
                classes = split_java_classes(source_code)
                for class_name, class_code in classes:
                    # 使用 文件路径::类名 作为模块 ID
                    full_module_id = f"{module_id}::{class_name}"
                    all_modules.append((full_module_id, class_code))
            else:
                all_modules.append((module_id, source_code))
        file_modules = all_modules
        print(f"Split into {len(file_modules)} modules (classes/files)")
    
    # 准备文本和模块 ID
    module_ids = [mid for mid, _ in file_modules]
    texts = [code for _, code in file_modules]
    
    print(f"\nTotal modules to process: {len(module_ids)}")

    # 设备选择
    if args.device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    print(f"Using device: {device}")

    # 加载模型
    print(f"Loading model: {args.model}")
    print("This may take a while on first run (downloading model)...")
    
    try:
        # 尝试加载 MLM 模型（用于计算困惑度）
        model = AutoModelForMaskedLM.from_pretrained(
            args.model,
            cache_dir=args.cache_dir,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            args.model,
            cache_dir=args.cache_dir,
        )
        is_mlm = True
    except Exception:
        # 回退到普通模型
        print("Warning: Could not load MLM model, using base model (perplexity metrics unavailable)")
        model = AutoModel.from_pretrained(
            args.model,
            cache_dir=args.cache_dir,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            args.model,
            cache_dir=args.cache_dir,
        )
        is_mlm = False
    
    model = model.to(device)
    model.eval()
    print("Model loaded successfully")

    # 解析层索引
    layer_indices = None
    if args.layers:
        if args.layers in ["low", "mid", "high"]:
            # 特殊处理：低/中/高层
            n_layers = model.config.num_hidden_layers if hasattr(model.config, 'num_hidden_layers') else 12
            if args.layers == "low":
                layer_indices = list(range(0, n_layers // 3))
            elif args.layers == "mid":
                layer_indices = list(range(n_layers // 3, 2 * n_layers // 3))
            elif args.layers == "high":
                layer_indices = list(range(2 * n_layers // 3, n_layers))
        else:
            layer_indices = [int(x.strip()) for x in args.layers.split(",")]

    # 解析要计算的指标
    metrics_to_compute = set(args.metrics.split(","))

    os.makedirs(os.path.dirname(args.out_prefix) if os.path.dirname(args.out_prefix) else ".", exist_ok=True)

    # 1. Attention 权重（工程级 attention 耦合矩阵）
    if "attention" in metrics_to_compute or "all" in metrics_to_compute:
        print("\n=== Computing Attention-based Coupling Matrix ===")
        att_matrix = compute_attention_coupling_matrix(
            model,
            tokenizer,
            texts,
            device=device,
            max_length=args.max_length,
        )
        save_matrix_csv(f"{args.out_prefix}_attention.csv", module_ids, att_matrix)
        print(f"Saved attention coupling matrix to: {args.out_prefix}_attention.csv")

    # 2. Token Embedding
    if "embedding" in metrics_to_compute or "all" in metrics_to_compute:
        print("\n=== Computing Token Embeddings ===")
        embeddings = []
        with torch.no_grad():
            for i in range(0, len(texts), args.batch_size):
                batch_texts = texts[i:i + args.batch_size]
                inputs = tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=args.max_length,
                ).to(device)

                outputs = model(**inputs, output_hidden_states=True)
                # 兼容 AutoModel 和 AutoModelForMaskedLM：
                # 优先使用 hidden_states[-1]，否则退回 last_hidden_state
                hidden_states = getattr(outputs, "hidden_states", None)
                if hidden_states is not None:
                    hidden = hidden_states[-1]
                else:
                    hidden = outputs.last_hidden_state
                # Mean pooling
                attention_mask = inputs["attention_mask"]
                mask_expanded = attention_mask.unsqueeze(-1).expand(hidden.size()).float()
                sum_embeddings = torch.sum(hidden * mask_expanded, dim=1)
                sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
                mean_pooled = sum_embeddings / sum_mask
                embeddings.append(mean_pooled.cpu().numpy())
        
        embeddings = np.vstack(embeddings)
        print(f"Computed embeddings shape: {embeddings.shape}")
        
        # 计算相似度矩阵
        similarity_matrix = cosine_similarity(embeddings)
        similarity_matrix = (similarity_matrix + 1.0) / 2.0  # 归一化到 [0, 1]
        
        save_matrix_csv(f"{args.out_prefix}_embedding.csv", module_ids, similarity_matrix)
        print(f"Saved embedding similarity matrix to: {args.out_prefix}_embedding.csv")

    # 3. Perplexity Metrics
    if "perplexity" in metrics_to_compute or "all" in metrics_to_compute:
        if is_mlm:
            print("\n=== Computing Perplexity Metrics ===")
            perplexity_data = compute_perplexity_metrics(
                model,
                tokenizer,
                texts,
                device=device,
            )
            print(f"Computed perplexity for {len(perplexity_data['module_perplexity'])} modules")
            print(f"Average perplexity: {perplexity_data['module_perplexity'].mean():.4f}")
            print(f"Average internal consistency: {perplexity_data['internal_consistency'].mean():.4f}")
        else:
            print("\n=== Skipping Perplexity Metrics (model is not MLM) ===")

    # 4. Layer-wise Semantic Coupling
    if "layer_wise" in metrics_to_compute or "all" in metrics_to_compute:
        print("\n=== Computing Layer-wise Semantic Coupling ===")
        layer_coupling = compute_layer_wise_semantic_coupling(
            model,
            tokenizer,
            texts,
            device=device,
            layer_indices=layer_indices,
        )
        
        save_matrix_csv(f"{args.out_prefix}_low_layer.csv", module_ids, layer_coupling["low_layer_coupling"])
        save_matrix_csv(f"{args.out_prefix}_mid_layer.csv", module_ids, layer_coupling["mid_layer_coupling"])
        save_matrix_csv(f"{args.out_prefix}_high_layer.csv", module_ids, layer_coupling["high_layer_coupling"])
        print(f"Saved layer-wise coupling matrices")

    print("\n=== Completed ===")
    print(f"Output prefix: {args.out_prefix}")


if __name__ == "__main__":
    main()

