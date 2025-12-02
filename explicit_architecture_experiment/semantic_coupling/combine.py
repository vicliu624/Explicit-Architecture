from typing import Dict, List

from .models import ModuleRecord, SCMatrices
from .struct_coupling import compute_S_struct
from .lex_coupling import compute_S_lex
from .sem_coupling import compute_S_sem_from_embs


def compute_semantic_coupling(
    modules: List[ModuleRecord],
    edge_type_weights: Dict[str, float],
    alpha: float = 0.4,
    beta: float = 0.2,
    gamma: float = 0.4,
) -> SCMatrices:
    """
    综合计算 S_struct / S_lex / S_sem 并按权重合成为 SC。

    对应文档中的公式：
        SC(i,j) = alpha * S_struct(i,j)
                + beta  * S_lex(i,j)
                + gamma * S_sem(i,j)
    其中 alpha + beta + gamma = 1。
    """
    if abs(alpha + beta + gamma - 1.0) > 1e-6:
        raise ValueError("alpha + beta + gamma must equal 1")

    S_struct = compute_S_struct(modules, edge_type_weights)
    S_lex = compute_S_lex(modules)
    S_sem = compute_S_sem_from_embs(modules)

    SC = alpha * S_struct + beta * S_lex + gamma * S_sem

    module_ids = [m.id for m in modules]
    return SCMatrices(
        modules=module_ids,
        S_struct=S_struct,
        S_lex=S_lex,
        S_sem=S_sem,
        SC=SC,
    )


