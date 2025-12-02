from typing import List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .models import ModuleRecord


def _embs_from_records(modules: List[ModuleRecord]) -> np.ndarray:
    """从模块记录中收集 embedding，并堆叠为 (N, D) 矩阵。"""
    embs = []
    for m in modules:
        if m.embedding is None:
            raise ValueError(f"Module {m.id} missing embedding")
        embs.append(np.asarray(m.embedding, dtype=float))
    return np.stack(embs, axis=0)


def compute_S_sem_from_embs(modules: List[ModuleRecord]) -> np.ndarray:
    """
    在已给出 embedding 的前提下，计算 S_sem(i,j)。

    使用余弦相似度并映射到 [0,1]。
    """
    X = _embs_from_records(modules)   # (N, D)
    S = cosine_similarity(X)         # ∈ [-1,1]
    S = (S + 1.0) / 2.0              # 映射到 [0,1]
    return S


def compute_embeddings_inplace(
    modules: List[ModuleRecord],
    model_name: str = "microsoft/codebert-base",
    batch_size: int = 16,
    device: Optional[str] = None,
    cache_dir: Optional[str] = None,
) -> None:
    """
    使用 sentence-transformers 在 Python 侧计算模块级 embedding。

    将结果直接写回 ModuleRecord.embedding。

    Parameters
    ----------
    cache_dir : Optional[str]
        模型缓存目录。如果提供，会优先从该目录加载模型，避免重复下载。
        例如: ".cache/models" 或 "C:/Users/.../.cache/sentence-transformers"
    """
    from sentence_transformers import SentenceTransformer
    import os

    texts = [m.text or "" for m in modules]
    
    # 如果指定了 cache_dir，尝试从本地加载
    if cache_dir and os.path.exists(cache_dir):
        # 检查是否是本地路径（包含 / 或 \）
        if os.path.sep in model_name or os.path.altsep in model_name:
            model_path = model_name
        else:
            # 尝试在 cache_dir 下找模型
            model_path = os.path.join(cache_dir, model_name.replace("/", "_"))
            if not os.path.exists(model_path):
                model_path = model_name  # 回退到原始名称
    else:
        model_path = model_name
    
    # 加载模型（sentence-transformers 会自动缓存到 ~/.cache/sentence-transformers）
    model = SentenceTransformer(model_path, device=device, cache_folder=cache_dir)
    
    # 如果指定了 cache_dir 且模型是从 HuggingFace 下载的，保存到本地以便下次使用
    if cache_dir and not os.path.exists(os.path.join(cache_dir, model_name.replace("/", "_"))):
        os.makedirs(cache_dir, exist_ok=True)
        local_model_path = os.path.join(cache_dir, model_name.replace("/", "_"))
        model.save(local_model_path)
        print(f"Model saved to {local_model_path} for future use")
    
    embs = model.encode(texts, batch_size=batch_size, show_progress_bar=True)

    for m, e in zip(modules, embs):
        m.embedding = e.tolist()


