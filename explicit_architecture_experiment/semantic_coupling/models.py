from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np


@dataclass
class ModuleRecord:
    """
    单个模块（通常为一个类）的信息。

    Attributes
    ----------
    id:
        模块唯一标识，建议使用 fully-qualified class 名
        （例如 "com.example.user.UserService"）。
    text:
        用于词汇与语义表示的文本：
        - 类名 / 方法名 / 参数名
        - Javadoc / 注释
        - 其他你认为有用的字符串
    deps:
        结构依赖信息：
        edge_type -> { target_module_id -> count }
        例如:
        {
            "call":   {"com.example.repo.UserRepo": 12},
            "field":  {"com.example.model.User": 3},
            "inherit":{"com.example.base.BaseService": 1}
        }
    embedding:
        可选：预先计算好的语义向量（如 CodeBERT / GraphCodeBERT）。
        若为空，可在 Python 侧通过 sentence-transformers 计算。
    """

    id: str
    text: str
    deps: Dict[str, Dict[str, int]]
    embedding: Optional[List[float]] = None


@dataclass
class SCMatrices:
    """
    语义耦合度相关矩阵。

    所有矩阵的行列顺序均与 `modules` 一致。
    """

    modules: List[str]
    S_struct: np.ndarray  # 结构耦合矩阵
    S_lex: np.ndarray     # 词汇耦合矩阵
    S_sem: np.ndarray     # 语义相似度矩阵
    SC: np.ndarray        # 综合语义耦合矩阵


