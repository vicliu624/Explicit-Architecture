"""
评估项目耦合度的综合工具。

对比结构、词汇、语义三种耦合度，给出项目解耦情况的综合评价。
"""

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def load_matrix_csv(path: str) -> Tuple[List[str], np.ndarray]:
    """从 CSV 文件加载矩阵。"""
    df = pd.read_csv(path, index_col=0)
    modules = df.index.tolist()
    matrix = df.values.astype(float)
    return modules, matrix


def analyze_coupling_health(
    modules: List[str],
    struct_matrix: np.ndarray,
    lex_matrix: np.ndarray,
    sem_matrix: np.ndarray,
    sc_matrix: np.ndarray,
) -> Dict:
    """
    综合分析项目的耦合健康度。

    Returns
    -------
    Dict with evaluation results
    """
    n = len(modules)
    off_diag_mask = ~np.eye(n, dtype=bool)
    
    # 排除对角线
    struct_off = struct_matrix[off_diag_mask]
    lex_off = lex_matrix[off_diag_mask]
    sem_off = sem_matrix[off_diag_mask]
    sc_off = sc_matrix[off_diag_mask]
    
    # 计算各类型耦合的统计
    def calc_stats(arr, name):
        return {
            f"{name}_mean": float(np.mean(arr)),
            f"{name}_median": float(np.median(arr)),
            f"{name}_std": float(np.std(arr)),
            f"{name}_max": float(np.max(arr)),
            f"{name}_p95": float(np.percentile(arr, 95)),
            f"{name}_p99": float(np.percentile(arr, 99)),
            f"{name}_strong_ties": int(np.sum(arr > 0.5)),
            f"{name}_moderate_ties": int(np.sum((arr > 0.2) & (arr <= 0.5))),
            f"{name}_weak_ties": int(np.sum(arr < 0.1)),
        }
    
    struct_stats = calc_stats(struct_off, "struct")
    lex_stats = calc_stats(lex_off, "lex")
    sem_stats = calc_stats(sem_off, "sem")
    sc_stats = calc_stats(sc_off, "sc")
    
    # 计算耦合健康度评分（0-100，越高越好）
    # 评分标准：
    # - 平均耦合度低（< 0.1）：+30 分
    # - 强耦合对少（< 总对数的 0.1%）：+30 分
    # - 中位数低（< 0.05）：+20 分
    # - 标准差适中（不过度集中也不过度分散）：+20 分
    
    total_pairs = n * (n - 1) / 2
    
    score = 0.0
    reasons = []
    
    # 平均耦合度评分
    if sc_stats["sc_mean"] < 0.05:
        score += 30
        reasons.append("✓ 平均耦合度极低 (< 0.05)")
    elif sc_stats["sc_mean"] < 0.1:
        score += 20
        reasons.append("✓ 平均耦合度较低 (< 0.1)")
    elif sc_stats["sc_mean"] < 0.2:
        score += 10
        reasons.append("⚠ 平均耦合度中等 (< 0.2)")
    else:
        reasons.append("✗ 平均耦合度较高 (>= 0.2)")
    
    # 强耦合对评分
    strong_ratio = sc_stats["sc_strong_ties"] / total_pairs
    if strong_ratio < 0.001:
        score += 30
        reasons.append(f"✓ 强耦合对极少 ({sc_stats['sc_strong_ties']} 对, < 0.1%)")
    elif strong_ratio < 0.01:
        score += 20
        reasons.append(f"✓ 强耦合对较少 ({sc_stats['sc_strong_ties']} 对, < 1%)")
    elif strong_ratio < 0.05:
        score += 10
        reasons.append(f"⚠ 强耦合对中等 ({sc_stats['sc_strong_ties']} 对, < 5%)")
    else:
        reasons.append(f"✗ 强耦合对较多 ({sc_stats['sc_strong_ties']} 对, >= 5%)")
    
    # 中位数评分
    if sc_stats["sc_median"] < 0.01:
        score += 20
        reasons.append("✓ 中位数极低 (< 0.01)，大部分模块对无耦合")
    elif sc_stats["sc_median"] < 0.05:
        score += 15
        reasons.append("✓ 中位数较低 (< 0.05)")
    elif sc_stats["sc_median"] < 0.1:
        score += 10
        reasons.append("⚠ 中位数中等 (< 0.1)")
    else:
        reasons.append("✗ 中位数较高 (>= 0.1)")
    
    # 标准差评分（适中的标准差表示耦合分布合理）
    if 0.01 < sc_stats["sc_std"] < 0.1:
        score += 20
        reasons.append("✓ 耦合度分布合理")
    elif sc_stats["sc_std"] < 0.01:
        score += 10
        reasons.append("⚠ 耦合度分布过于集中")
    else:
        score += 10
        reasons.append("⚠ 耦合度分布较分散")
    
    # 结构 vs 语义耦合对比
    struct_sem_diff = struct_stats["struct_mean"] - sem_stats["sem_mean"]
    if abs(struct_sem_diff) < 0.05:
        reasons.append("✓ 结构耦合与语义耦合一致，架构清晰")
    elif struct_sem_diff > 0.1:
        reasons.append("⚠ 结构耦合明显高于语义耦合，可能存在过度设计")
    elif struct_sem_diff < -0.1:
        reasons.append("⚠ 语义耦合明显高于结构耦合，可能存在隐式依赖")
    
    return {
        "num_modules": n,
        "total_pairs": int(total_pairs),
        "health_score": min(100, max(0, score)),
        "reasons": reasons,
        "struct": struct_stats,
        "lex": lex_stats,
        "sem": sem_stats,
        "sc": sc_stats,
    }


def print_evaluation(result: Dict) -> None:
    """打印评估结果。"""
    print("\n" + "=" * 70)
    print("项目耦合度健康评估")
    print("=" * 70)
    
    print(f"\n模块数量: {result['num_modules']}")
    print(f"模块对总数: {result['total_pairs']:,}")
    print(f"\n健康度评分: {result['health_score']:.1f}/100")
    
    if result['health_score'] >= 80:
        print("评级: 优秀 ⭐⭐⭐⭐⭐")
    elif result['health_score'] >= 60:
        print("评级: 良好 ⭐⭐⭐⭐")
    elif result['health_score'] >= 40:
        print("评级: 中等 ⭐⭐⭐")
    else:
        print("评级: 需要改进 ⭐⭐")
    
    print("\n评估要点:")
    for reason in result['reasons']:
        print(f"  {reason}")
    
    print("\n" + "-" * 70)
    print("详细统计")
    print("-" * 70)
    
    print("\n【结构耦合 (S_struct)】")
    s = result['struct']
    print(f"  平均: {s['struct_mean']:.6f} | 中位数: {s['struct_median']:.6f} | 最大: {s['struct_max']:.6f}")
    print(f"  强耦合 (>0.5): {s['struct_strong_ties']} 对 | 中等 (0.2-0.5): {s['struct_moderate_ties']} 对")
    
    print("\n【词汇耦合 (S_lex)】")
    l = result['lex']
    print(f"  平均: {l['lex_mean']:.6f} | 中位数: {l['lex_median']:.6f} | 最大: {l['lex_max']:.6f}")
    print(f"  强耦合 (>0.5): {l['lex_strong_ties']} 对 | 中等 (0.2-0.5): {l['lex_moderate_ties']} 对")
    
    print("\n【语义耦合 (S_sem)】")
    se = result['sem']
    print(f"  平均: {se['sem_mean']:.6f} | 中位数: {se['sem_median']:.6f} | 最大: {se['sem_max']:.6f}")
    print(f"  强耦合 (>0.5): {se['sem_strong_ties']} 对 | 中等 (0.2-0.5): {se['sem_moderate_ties']} 对")
    
    print("\n【综合耦合 (SC)】")
    sc = result['sc']
    print(f"  平均: {sc['sc_mean']:.6f} | 中位数: {sc['sc_median']:.6f} | 最大: {sc['sc_max']:.6f}")
    print(f"  95%分位: {sc['sc_p95']:.6f} | 99%分位: {sc['sc_p99']:.6f}")
    print(f"  强耦合 (>0.5): {sc['sc_strong_ties']} 对 | 中等 (0.2-0.5): {sc['sc_moderate_ties']} 对")
    
    print("\n" + "=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate project coupling health from all matrix files",
    )
    parser.add_argument(
        "--prefix",
        required=True,
        help="Prefix of matrix files (e.g., out/ynjtgs-command-center)",
    )
    
    args = parser.parse_args()
    
    prefix = Path(args.prefix)
    base_dir = prefix.parent
    base_name = prefix.name
    
    # 加载所有矩阵
    print(f"Loading matrices from: {base_dir}")
    
    struct_path = base_dir / f"{base_name}_S_struct.csv"
    lex_path = base_dir / f"{base_name}_S_lex.csv"
    sem_path = base_dir / f"{base_name}_S_sem.csv"
    sc_path = base_dir / f"{base_name}_SC.csv"
    
    print(f"  Loading {struct_path.name}...")
    modules, struct_matrix = load_matrix_csv(str(struct_path))
    
    print(f"  Loading {lex_path.name}...")
    _, lex_matrix = load_matrix_csv(str(lex_path))
    
    print(f"  Loading {sem_path.name}...")
    _, sem_matrix = load_matrix_csv(str(sem_path))
    
    print(f"  Loading {sc_path.name}...")
    _, sc_matrix = load_matrix_csv(str(sc_path))
    
    # 分析
    print(f"\nAnalyzing {len(modules)} modules...")
    result = analyze_coupling_health(
        modules, struct_matrix, lex_matrix, sem_matrix, sc_matrix
    )
    
    # 打印结果
    print_evaluation(result)


if __name__ == "__main__":
    main()

