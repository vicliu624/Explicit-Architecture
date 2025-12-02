from __future__ import annotations

import csv
import json
from typing import Dict, List, Tuple

import numpy as np

from .models import ModuleRecord, SCMatrices


def load_modules_from_json(path: str) -> Tuple[List[ModuleRecord], Dict[str, float]]:
    """
    从 JSON 文件加载模块与结构依赖信息。

    期望的 JSON 结构示例::

        {
          "edge_type_weights": {
            "call": 1.0,
            "field": 0.8,
            "inherit": 0.9
          },
          "modules": [
            {
              "id": "com.example.user.UserService",
              "text": "class UserService { ... } // 注释等",
              "deps": {
                "call":   {"com.example.repo.UserRepo": 12},
                "inherit":{"com.example.base.BaseService": 1}
              },
              "embedding": [0.12, -0.03, ...]   # 可选
            }
          ]
        }
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    edge_w: Dict[str, float] = data.get("edge_type_weights", {})

    modules: List[ModuleRecord] = []
    for m in data.get("modules", []):
        modules.append(
            ModuleRecord(
                id=m["id"],
                text=m.get("text", ""),
                deps=m.get("deps", {}) or {},
                embedding=m.get("embedding"),
            )
        )

    return modules, edge_w


def save_matrix_csv(path: str, modules: List[str], M: np.ndarray) -> None:
    """以 CSV 形式保存矩阵，首行首列写入模块 ID。"""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([""] + modules)
        for mid, row in zip(modules, M):
            writer.writerow([mid] + list(map(float, row)))


def save_sc_matrices(prefix: str, sc: SCMatrices) -> None:
    """
    以四个 CSV 文件的形式保存所有矩阵:
      - {prefix}_S_struct.csv
      - {prefix}_S_lex.csv
      - {prefix}_S_sem.csv
      - {prefix}_SC.csv
    """
    save_matrix_csv(f"{prefix}_S_struct.csv", sc.modules, sc.S_struct)
    save_matrix_csv(f"{prefix}_S_lex.csv", sc.modules, sc.S_lex)
    save_matrix_csv(f"{prefix}_S_sem.csv", sc.modules, sc.S_sem)
    save_matrix_csv(f"{prefix}_SC.csv", sc.modules, sc.SC)


