from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import ModuleRecord


def compute_S_lex(modules: List[ModuleRecord]) -> np.ndarray:
    """
    计算词汇耦合度矩阵 S_lex(i,j)。

    做法：
      1. 将每个模块的 text 字段视为文档
      2. 使用 TF–IDF 向量表示
      3. 计算文档间余弦相似度
    """
    texts = [m.text or "" for m in modules]

    # 如果所有文本都为空，则返回单位矩阵（完全未知，且不影响后续归一化）
    if not any(t.strip() for t in texts):
        return np.eye(len(modules), dtype=float)

    vectorizer = TfidfVectorizer(
        max_features=8000,
        token_pattern=r"[A-Za-z_][A-Za-z0-9_]*",
        lowercase=True,
    )
    X = vectorizer.fit_transform(texts)  # (N, D)
    S = cosine_similarity(X)            # ∈ [0,1]（TF–IDF 非负）
    return S


