from typing import Dict, List

import numpy as np

from .models import ModuleRecord


def compute_S_struct(
    modules: List[ModuleRecord],
    edge_type_weights: Dict[str, float],
) -> np.ndarray:
    """
    计算结构耦合度矩阵 S_struct(i,j)。

    对应《一、目标（精炼）.md》中结构耦合的定义：
      - 以各类静态依赖为边
      - 为每种边类型赋予权重 w_t
      - 对 (i,j) 求加权和并归一化到 [0,1]
    """
    n = len(modules)
    index = {m.id: idx for idx, m in enumerate(modules)}

    S = np.zeros((n, n), dtype=float)

    for i, m in enumerate(modules):
        deps = m.deps or {}
        for edge_type, targets in deps.items():
            w = float(edge_type_weights.get(edge_type, 1.0))
            for tgt_id, count in (targets or {}).items():
                j = index.get(tgt_id)
                if j is None:
                    continue
                S[i, j] += w * float(count)

    max_val = float(S.max())
    if max_val > 0.0:
        S /= max_val

    return S


