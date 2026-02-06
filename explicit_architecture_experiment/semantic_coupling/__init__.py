"""
语义耦合度（Semantic Coupling）核心库。

新思路：直接从 Transformer 内部机制提取指标，不依赖 AST、调用图。
"""

from .io import save_matrix_csv
from .transformer_metrics import (
    compute_perplexity_metrics,
    compute_layer_wise_semantic_coupling,
)

__all__ = [
    "save_matrix_csv",
    "compute_perplexity_metrics",
    "compute_layer_wise_semantic_coupling",
]


