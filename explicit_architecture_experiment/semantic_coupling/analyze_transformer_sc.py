"""
CLI 工具：分析通过 Transformer 计算得到的耦合矩阵 CSV。

功能：
- 读取任意一个矩阵 CSV（首行首列为模块 ID）
- 输出 Top-K 高耦合模块对
- 计算每个模块的总耦合度（行和）分布
- 计算全局统计（平均、标准差、Gini 系数）
- 以文本形式打印简洁报告，适合在 PowerShell 中直接查看
"""

import argparse
from typing import List, Tuple

import numpy as np
import pandas as pd


def compute_gini(values: np.ndarray) -> float:
    """计算 Gini 系数。

    values: 一维非负数组。
    """
    x = np.asarray(values, dtype=float)
    x = x[x >= 0]
    if x.size == 0:
        return 0.0
    if np.allclose(x, 0):
        return 0.0

    x_sorted = np.sort(x)
    n = x_sorted.size
    cumx = np.cumsum(x_sorted)
    gini = (n + 1 - 2 * np.sum(cumx) / cumx[-1]) / n
    return float(gini)


def find_top_pairs(
    M: np.ndarray,
    modules: List[str],
    k: int = 50,
    min_value: float = 0.0,
) -> List[Tuple[str, str, float]]:
    """从对称矩阵中找出 Top-K 模块对（只看上三角，去掉自耦合）。"""
    n = len(modules)
    pairs: List[Tuple[str, str, float]] = []

    for i in range(n):
        for j in range(i + 1, n):
            v = float(M[i, j])
            if v >= min_value:
                pairs.append((modules[i], modules[j], v))

    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs[:k]


def print_report(
    matrix_path: str,
    top_k: int,
    min_value: float,
    focus_modules: List[str] | None = None,
) -> None:
    print(f"Loading matrix from: {matrix_path}")
    df = pd.read_csv(matrix_path, index_col=0)

    modules = list(df.index)
    M = df.to_numpy(dtype=float)

    print(f"Matrix shape: {M.shape[0]} x {M.shape[1]}")

    # 行和作为“总耦合度”（去掉自耦合对角线）
    row_sums = M.sum(axis=1) - np.diag(M)

    avg = float(row_sums.mean())
    std = float(row_sums.std())
    gini = compute_gini(row_sums)

    print("\n=== Global Stats (Row-sum Coupling) ===")
    print(f"Mean total coupling  : {avg:.6f}")
    print(f"Std  total coupling  : {std:.6f}")
    print(f"Gini(total coupling) : {gini:.6f}")

    # 找出 Top-K 模块对
    top_pairs = find_top_pairs(M, modules, k=top_k, min_value=min_value)

    print("\n=== Top Coupled Module Pairs ===")
    print(f"(Top {len(top_pairs)}, threshold >= {min_value})")
    for a, b, v in top_pairs:
        print(f"{v:.6f}\t{a}\t<->\t{b}")

    # 打印一些“高耦合”模块（按行和排序）
    idx_sorted = np.argsort(-row_sums)
    print("\n=== Top Modules by Total Coupling ===")
    for i in idx_sorted[: min(20, len(idx_sorted))]:
        print(f"{row_sums[i]:.6f}\t{modules[i]}")

    # 若指定了关注的模块，分别打印它们的 Top-K 邻居
    if focus_modules:
        name_to_idx = {m: idx for idx, m in enumerate(modules)}
        print("\n=== Neighbors for Focus Modules ===")
        for name in focus_modules:
            idx = name_to_idx.get(name)
            if idx is None:
                print(f"[WARN] focus module not found in matrix: {name}")
                continue
            row = M[idx].copy()
            row[idx] = -1.0  # 排除自耦合
            neighbor_indices = np.argsort(-row)[: min(top_k, len(row))]
            print(f"\n-- {name} --")
            for j in neighbor_indices:
                if row[j] < min_value:
                    continue
                print(f"{row[j]:.6f}\t{name}\t<->\t{modules[j]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="分析 Transformer 耦合矩阵 CSV（embedding / layer-wise 等）",
    )
    parser.add_argument(
        "--matrix",
        required=True,
        help="矩阵 CSV 路径（如 out/transformer_sc_embedding.csv）",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=50,
        help="输出 Top-K 模块对（默认 50）",
    )
    parser.add_argument(
        "--min-value",
        type=float,
        default=0.0,
        help="只展示耦合度 >= 此值的模块对（默认 0.0）",
    )
    parser.add_argument(
        "--focus-module",
        action="append",
        default=None,
        help="关注的模块 ID，可多次指定，打印它们各自的 Top-K 邻居",
    )

    args = parser.parse_args()

    print_report(
        matrix_path=args.matrix,
        top_k=args.top_k,
        min_value=args.min_value,
        focus_modules=args.focus_module,
    )


if __name__ == "__main__":
    main()