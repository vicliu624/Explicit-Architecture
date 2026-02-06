"""
从 Transformer 内部机制直接提取语义耦合度指标。

核心思路：
1. 利用 Attention 权重：模块内/跨模块关注度
2. 利用 Token Embedding：模块间语义相似度
3. 利用层级表示：不同层捕捉不同粒度的语义
4. 利用预测困惑度：模块内部一致性

不依赖 AST、调用图等传统中间表示，只依赖 Transformer 的语义捕捉能力。
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel, AutoModelForMaskedLM


def extract_attention_weights(
    model,
    tokenizer,
    texts: List[str],
    device: str = "cpu",
    layer_indices: Optional[List[int]] = None,
    head_indices: Optional[List[int]] = None,
) -> Dict[str, np.ndarray]:
    """
    从 Transformer 模型提取 attention 权重矩阵。
    
    TODO: 实现 token 到模块的映射逻辑后，用于计算模块间 attention 耦合。
    
    Returns
    -------
    Dict[str, np.ndarray]
        {
            "attention_matrices": List[np.ndarray],  # 每个文本的 attention 矩阵列表
            "token_embeddings": np.ndarray,  # [n_texts, max_seq_len, hidden_dim]
            "token_ids": List[List[int]],  # 每个文本的 token IDs
        }
    """
    model.eval()
    attention_matrices = []
    token_embeddings_list = []
    token_ids_list = []
    
    with torch.no_grad():
        for text in texts:
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(device)
            
            token_ids_list.append(inputs["input_ids"][0].cpu().numpy().tolist())
            
            outputs = model(**inputs, output_attentions=True, output_hidden_states=True)
            
            attentions = outputs.attentions
            if layer_indices is None:
                layer_indices = list(range(len(attentions)))
            if head_indices is None:
                head_indices = list(range(attentions[0].shape[1]))
            
            layer_attentions = []
            for layer_idx in layer_indices:
                layer_attn = attentions[layer_idx][0]
                head_attn = layer_attn[head_indices].mean(dim=0)
                layer_attentions.append(head_attn.cpu().numpy())
            
            avg_attention = np.mean(layer_attentions, axis=0)
            attention_matrices.append(avg_attention)
            
            hidden_states = outputs.hidden_states[-1]
            token_embeddings_list.append(hidden_states[0].cpu().numpy())
    
    max_len = max(emb.shape[0] for emb in token_embeddings_list)
    hidden_dim = token_embeddings_list[0].shape[1]
    padded_embeddings = np.zeros((len(texts), max_len, hidden_dim))
    for i, emb in enumerate(token_embeddings_list):
        padded_embeddings[i, :emb.shape[0], :] = emb
    
    return {
        "attention_matrices": attention_matrices,
        "token_embeddings": padded_embeddings,
        "token_ids": token_ids_list,
    }


def compute_perplexity_metrics(
    model,
    tokenizer,
    texts: List[str],
    device: str = "cpu",
) -> Dict[str, np.ndarray]:
    """
    计算每个模块的预测困惑度指标。
    
    困惑度低 → 模块内部语义一致性高
    困惑度高 → 模块内部语义不一致或依赖外部上下文
    
    Returns
    -------
    Dict[str, np.ndarray]
        {
            "per_token_loss": List[np.ndarray],  # 每个 token 的 loss
            "module_perplexity": np.ndarray,  # 每个模块的平均困惑度
            "internal_consistency": np.ndarray,  # 模块内部一致性（低困惑度 = 高一致性）
        }
    """
    if not isinstance(model, AutoModelForMaskedLM):
        # 如果不是 MLM 模型，无法直接计算困惑度
        return {
            "per_token_loss": [],
            "module_perplexity": np.array([]),
            "internal_consistency": np.array([]),
        }
    
    model.eval()
    per_token_losses = []
    module_perplexities = []
    
    with torch.no_grad():
        for text in texts:
            # Tokenize
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(device)
            
            # Forward pass
            outputs = model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss  # Average loss
            
            # Per-token loss (需要手动计算)
            logits = outputs.logits  # [batch_size, seq_len, vocab_size]
            labels = inputs["input_ids"]  # [batch_size, seq_len]
            
            # Compute per-token cross-entropy loss
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            loss_fct = torch.nn.CrossEntropyLoss(reduction='none', ignore_index=tokenizer.pad_token_id)
            per_token_loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            per_token_loss = per_token_loss.view(shift_labels.size())
            
            per_token_losses.append(per_token_loss[0].cpu().numpy())
            
            # Perplexity = exp(loss)
            perplexity = torch.exp(loss).item()
            module_perplexities.append(perplexity)
    
    module_perplexities = np.array(module_perplexities)
    
    # 内部一致性：低困惑度 = 高一致性
    # 归一化到 [0, 1]，困惑度越低，一致性越高
    max_perplexity = module_perplexities.max() if len(module_perplexities) > 0 else 1.0
    internal_consistency = 1.0 - (module_perplexities / max_perplexity) if max_perplexity > 0 else np.zeros_like(module_perplexities)
    
    return {
        "per_token_loss": per_token_losses,
        "module_perplexity": module_perplexities,
        "internal_consistency": internal_consistency,
    }


def compute_layer_wise_semantic_coupling(
    model,
    tokenizer,
    module_texts: List[str],
    device: str = "cpu",
    layer_indices: Optional[List[int]] = None,
) -> Dict[str, np.ndarray]:
    """
    利用不同层的输出计算不同粒度的语义耦合。
    
    低层：语法结构
    中层：函数/类调用模式
    高层：模块级语义
    
    Returns
    -------
    Dict[str, np.ndarray]
        {
            "low_layer_coupling": np.ndarray,  # 语法/结构耦合
            "mid_layer_coupling": np.ndarray,  # 调用模式耦合
            "high_layer_coupling": np.ndarray,  # 模块级语义耦合
        }
    """
    model.eval()
    n_modules = len(module_texts)
    
    # 获取模型层数
    n_layers = model.config.num_hidden_layers if hasattr(model.config, 'num_hidden_layers') else 12
    
    if layer_indices is None:
        # 默认：低层 = 前1/3，中层 = 中1/3，高层 = 后1/3
        low_layers = list(range(0, n_layers // 3))
        mid_layers = list(range(n_layers // 3, 2 * n_layers // 3))
        high_layers = list(range(2 * n_layers // 3, n_layers))
    else:
        low_layers = [i for i in layer_indices if i < n_layers // 3]
        mid_layers = [i for i in layer_indices if n_layers // 3 <= i < 2 * n_layers // 3]
        high_layers = [i for i in layer_indices if i >= 2 * n_layers // 3]
    
    # 提取各层的 token embeddings
    module_embeddings_low = []
    module_embeddings_mid = []
    module_embeddings_high = []
    
    with torch.no_grad():
        for text in module_texts:
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(device)
            
            outputs = model(**inputs, output_hidden_states=True)
            hidden_states = outputs.hidden_states  # List of [batch_size, seq_len, hidden_dim]
            
            # 提取各层的 [CLS] token embedding（或平均 pooling）
            if len(hidden_states) > 0:
                # Low layer: average of low layers
                low_emb = torch.stack([hidden_states[i][0, 0, :] for i in low_layers if i < len(hidden_states)]).mean(dim=0)
                module_embeddings_low.append(low_emb.cpu().numpy())
                
                # Mid layer: average of mid layers
                mid_emb = torch.stack([hidden_states[i][0, 0, :] for i in mid_layers if i < len(hidden_states)]).mean(dim=0)
                module_embeddings_mid.append(mid_emb.cpu().numpy())
                
                # High layer: average of high layers
                high_emb = torch.stack([hidden_states[i][0, 0, :] for i in high_layers if i < len(hidden_states)]).mean(dim=0)
                module_embeddings_high.append(high_emb.cpu().numpy())
    
    # 计算模块间相似度（余弦相似度）
    low_embeddings = np.array(module_embeddings_low)
    mid_embeddings = np.array(module_embeddings_mid)
    high_embeddings = np.array(module_embeddings_high)
    
    low_coupling = cosine_similarity(low_embeddings)
    mid_coupling = cosine_similarity(mid_embeddings)
    high_coupling = cosine_similarity(high_embeddings)
    
    # 归一化到 [0, 1]
    low_coupling = (low_coupling + 1.0) / 2.0
    mid_coupling = (mid_coupling + 1.0) / 2.0
    high_coupling = (high_coupling + 1.0) / 2.0
    
    return {
        "low_layer_coupling": low_coupling,
        "mid_layer_coupling": mid_coupling,
        "high_layer_coupling": high_coupling,
    }


def compute_attention_coupling_matrix(
    model,
    tokenizer,
    module_texts: List[str],
    device: str = "cpu",
    max_length: int = 512,
    max_tokens_per_module: int = 64,
    layer_indices: Optional[List[int]] = None,
    head_indices: Optional[List[int]] = None,
) -> np.ndarray:
    """
    计算基于 attention 的模块间耦合矩阵（工程级别，全项目）。

    思路：
    - 先对每个模块单独分词，截断到 max_tokens_per_module
    - 再按批次将多个模块的 token 拼接成一个长序列
    - 一次前向得到 self-attention 矩阵 A[seq_len, seq_len]
    - 按模块 span 聚合，得到模块 i -> j 的平均 attention
    - 所有 batch 的结果累加并归一化，得到全局模块间 attention 耦合矩阵

    注意：
    - 为控制复杂度，每个模块最多使用 max_tokens_per_module 个 token
    - 为避免 O(N^2) 前向，只在拼接后的长序列上做一次 attention 计算
    """
    model.eval()
    n_modules = len(module_texts)
    if n_modules == 0:
        return np.zeros((0, 0), dtype=float)

    # 第一步：预先为每个模块分词并截断
    print("\n[attention] Tokenizing modules...")
    all_token_ids: List[List[int]] = []
    for text in module_texts:
        inputs = tokenizer(
            text,
            add_special_tokens=False,
            return_tensors="pt",
            truncation=True,
            max_length=max_tokens_per_module,
        )
        ids = inputs["input_ids"][0].tolist()
        all_token_ids.append(ids[:max_tokens_per_module])

    # 初始化全局耦合矩阵与计数
    C = np.zeros((n_modules, n_modules), dtype=float)
    counts = np.zeros((n_modules, n_modules), dtype=float)

    # 默认使用所有层、所有 head
    n_heads_default: Optional[int] = None

    idx = 0
    batch_id = 0
    while idx < n_modules:
        batch_id += 1
        # 尝试在当前 batch 中塞入尽可能多的模块
        batch_indices: List[int] = []
        batch_token_ids: List[int] = []
        module_spans: List[Tuple[int, int]] = []  # (start, end) for each module in batch

        while idx < n_modules:
            mod_idx = idx
            tok_ids = all_token_ids[mod_idx]
            if not tok_ids:
                idx += 1
                continue

            # 如果再加入这个模块会超过 max_length，就结束当前 batch
            if len(batch_token_ids) + len(tok_ids) > max_length:
                break

            start = len(batch_token_ids)
            batch_token_ids.extend(tok_ids)
            end = len(batch_token_ids)

            batch_indices.append(mod_idx)
            module_spans.append((start, end))

            idx += 1

        if not batch_indices:
            # 单个模块就超过 max_length，只用前 max_length 个 token
            tok_ids = all_token_ids[idx]
            tok_ids = tok_ids[:max_length]
            batch_token_ids = tok_ids
            batch_indices = [idx]
            module_spans = [(0, len(tok_ids))]
            idx += 1

        print(f"[attention] Batch {batch_id}: {len(batch_indices)} modules, {len(batch_token_ids)} tokens")

        # 构造输入并前向
        input_ids = torch.tensor([batch_token_ids], dtype=torch.long, device=device)
        attention_mask = torch.ones_like(input_ids, device=device)

        with torch.no_grad():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=True,
            )
            attentions = outputs.attentions  # tuple(L) of [1, H, S, S]

        if layer_indices is None:
            layer_indices_eff = list(range(len(attentions)))
        else:
            layer_indices_eff = layer_indices

        if head_indices is None:
            if n_heads_default is None:
                n_heads_default = attentions[0].shape[1]
            head_indices_eff = list(range(n_heads_default))
        else:
            head_indices_eff = head_indices

        # 聚合层和 head，得到 [S, S]
        layer_mats = []
        for li in layer_indices_eff:
            layer_attn = attentions[li][0]  # [H, S, S]
            head_attn = layer_attn[head_indices_eff].mean(dim=0)  # [S, S]
            layer_mats.append(head_attn.cpu().numpy())
        A = np.mean(layer_mats, axis=0)  # [S, S]

        # 按模块 span 聚合，更新 C
        m_in_batch = len(batch_indices)
        for i_local in range(m_in_batch):
            i_global = batch_indices[i_local]
            s_i, e_i = module_spans[i_local]
            if e_i <= s_i:
                continue
            for j_local in range(m_in_batch):
                j_global = batch_indices[j_local]
                if i_global == j_global:
                    continue
                s_j, e_j = module_spans[j_local]
                if e_j <= s_j:
                    continue
                sub = A[s_i:e_i, s_j:e_j]
                if sub.size == 0:
                    continue
                val = float(sub.mean())
                C[i_global, j_global] += val
                counts[i_global, j_global] += 1.0

    # 归一化
    mask = counts > 0
    C[mask] /= counts[mask]

    # 将对角线设为 0（不关心自耦合）
    np.fill_diagonal(C, 0.0)

    return C

