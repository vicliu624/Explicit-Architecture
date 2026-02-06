"""
I/O 工具：保存矩阵到 CSV 文件。

新思路：不再需要从 JSON 加载，直接从源代码提取。
"""

from __future__ import annotations

import csv
from typing import List

import numpy as np


def save_matrix_csv(path: str, modules: List[str], M: np.ndarray) -> None:
    """以 CSV 形式保存矩阵，首行首列写入模块 ID。"""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([""] + modules)
        for mid, row in zip(modules, M):
            writer.writerow([mid] + list(map(float, row)))
