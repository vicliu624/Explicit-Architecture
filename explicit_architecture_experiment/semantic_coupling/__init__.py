"""
语义耦合度（Semantic Coupling）核心库。

本包实现《一、目标（精炼）.md》中定义的：
    - 结构耦合 S_struct
    - 词汇耦合 S_lex
    - 语义相似度 S_sem
    - 综合语义耦合度 SC
"""

from .models import ModuleRecord, SCMatrices
from .combine import compute_semantic_coupling
from .io import load_modules_from_json, save_sc_matrices

__all__ = [
    "ModuleRecord",
    "SCMatrices",
    "compute_semantic_coupling",
    "load_modules_from_json",
    "save_sc_matrices",
]


