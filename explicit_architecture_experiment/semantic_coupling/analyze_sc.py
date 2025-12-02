"""
分析语义耦合度矩阵的工具脚本。

提供以下功能：
1. 找出 top-k 强耦合的模块对
2. 生成可视化（热力图、网络图）
3. 统计分析
4. 导出为易读格式
"""

import argparse
import csv
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd


def load_matrix_csv(path: str) -> Tuple[List[str], np.ndarray]:
    """从 CSV 文件加载矩阵，返回模块列表和矩阵。"""
    df = pd.read_csv(path, index_col=0)
    modules = df.index.tolist()
    matrix = df.values.astype(float)
    return modules, matrix


def find_top_couplings(
    modules: List[str],
    matrix: np.ndarray,
    top_k: int = 50,
    exclude_self: bool = True,
) -> List[Tuple[str, str, float]]:
    """
    找出 top-k 强耦合的模块对。

    Returns
    -------
    List[Tuple[str, str, float]]
        [(module_i, module_j, coupling_value), ...]，按耦合度降序排列
    """
    n = len(modules)
    pairs = []

    for i in range(n):
        for j in range(n):
            if exclude_self and i == j:
                continue
            pairs.append((modules[i], modules[j], float(matrix[i, j])))

    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs[:top_k]


def analyze_matrix_stats(modules: List[str], matrix: np.ndarray) -> dict:
    """计算矩阵的统计信息。"""
    n = len(modules)
    # 排除对角线
    off_diag = matrix[~np.eye(n, dtype=bool)]

    return {
        "num_modules": n,
        "mean_coupling": float(np.mean(off_diag)),
        "median_coupling": float(np.median(off_diag)),
        "std_coupling": float(np.std(off_diag)),
        "max_coupling": float(np.max(off_diag)),
        "min_coupling": float(np.min(off_diag)),
        "num_strong_ties": int(np.sum(off_diag > 0.5)),  # 耦合度 > 0.5 的边数
        "num_weak_ties": int(np.sum(off_diag < 0.1)),   # 耦合度 < 0.1 的边数
    }


def export_top_couplings(
    pairs: List[Tuple[str, str, float]],
    output_path: str,
    matrix_type: str = "SC",
) -> None:
    """将 top-k 耦合对导出为 CSV。"""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Module_A", "Module_B", f"{matrix_type}_Coupling"])
        for rank, (m1, m2, val) in enumerate(pairs, 1):
            writer.writerow([rank, m1, m2, f"{val:.6f}"])


def print_stats(stats: dict, matrix_type: str = "SC") -> None:
    """打印统计信息。"""
    print(f"\n=== {matrix_type} Matrix Statistics ===")
    print(f"Number of modules: {stats['num_modules']}")
    print(f"Mean coupling: {stats['mean_coupling']:.6f}")
    print(f"Median coupling: {stats['median_coupling']:.6f}")
    print(f"Std coupling: {stats['std_coupling']:.6f}")
    print(f"Max coupling: {stats['max_coupling']:.6f}")
    print(f"Min coupling: {stats['min_coupling']:.6f}")
    print(f"Strong ties (coupling > 0.5): {stats['num_strong_ties']}")
    print(f"Weak ties (coupling < 0.1): {stats['num_weak_ties']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze semantic coupling matrices",
    )
    parser.add_argument(
        "--matrix",
        required=True,
        help="Path to matrix CSV file (e.g., out/ynjtgs-command-center_SC.csv)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=50,
        help="Number of top couplings to extract (default: 50)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for top-k couplings CSV (default: {matrix}_top{top_k}.csv)",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only print statistics, don't export top-k",
    )

    args = parser.parse_args()

    # 加载矩阵
    print(f"Loading matrix from: {args.matrix}")
    modules, matrix = load_matrix_csv(args.matrix)
    print(f"Loaded {len(modules)} modules")

    # 计算统计信息
    matrix_type = Path(args.matrix).stem.split("_")[-1]  # 从文件名提取类型
    stats = analyze_matrix_stats(modules, matrix)
    print_stats(stats, matrix_type)

    if args.stats_only:
        return

    # 找出 top-k 强耦合对
    print(f"\nFinding top-{args.top_k} couplings...")
    top_pairs = find_top_couplings(modules, matrix, top_k=args.top_k)

    # 打印前 10 个
    print(f"\n=== Top 10 Couplings ===")
    for rank, (m1, m2, val) in enumerate(top_pairs[:10], 1):
        print(f"{rank:3d}. {m1} <-> {m2}: {val:.6f}")

    # 导出
    output_path = args.output
    if output_path is None:
        base = Path(args.matrix).stem
        output_path = f"{base}_top{args.top_k}.csv"

    export_top_couplings(top_pairs, output_path, matrix_type)
    print(f"\nTop-{args.top_k} couplings exported to: {output_path}")


if __name__ == "__main__":
    main()

