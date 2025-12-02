"""
诊断代码质量问题的工具。

通过对比结构耦合、词汇耦合、语义耦合，判断语义耦合度高是工具问题还是代码质量问题。
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


def analyze_coupling_correlation(
    struct_matrix: np.ndarray,
    lex_matrix: np.ndarray,
    sem_matrix: np.ndarray,
) -> Dict:
    """
    分析三种耦合类型之间的相关性。
    
    如果语义耦合高但结构/词汇耦合低，可能是工具问题。
    如果三种耦合都高，可能是代码质量问题。
    """
    n = len(struct_matrix)
    off_diag_mask = ~np.eye(n, dtype=bool)
    
    struct_flat = struct_matrix[off_diag_mask]
    lex_flat = lex_matrix[off_diag_mask]
    sem_flat = sem_matrix[off_diag_mask]
    
    # 计算相关性
    struct_lex_corr = np.corrcoef(struct_flat, lex_flat)[0, 1]
    struct_sem_corr = np.corrcoef(struct_flat, sem_flat)[0, 1]
    lex_sem_corr = np.corrcoef(lex_flat, sem_flat)[0, 1]
    
    # 分析高语义耦合的模块对
    high_sem_mask = sem_flat > 0.9
    high_sem_count = np.sum(high_sem_mask)
    
    if high_sem_count > 0:
        high_sem_struct_mean = np.mean(struct_flat[high_sem_mask])
        high_sem_lex_mean = np.mean(lex_flat[high_sem_mask])
        high_sem_struct_high = np.sum(struct_flat[high_sem_mask] > 0.5)
        high_sem_lex_high = np.sum(lex_flat[high_sem_mask] > 0.5)
    else:
        high_sem_struct_mean = 0
        high_sem_lex_mean = 0
        high_sem_struct_high = 0
        high_sem_lex_high = 0
    
    return {
        "struct_lex_correlation": float(struct_lex_corr),
        "struct_sem_correlation": float(struct_sem_corr),
        "lex_sem_correlation": float(lex_sem_corr),
        "high_sem_count": int(high_sem_count),
        "high_sem_struct_mean": float(high_sem_struct_mean),
        "high_sem_lex_mean": float(high_sem_lex_mean),
        "high_sem_struct_high_ratio": float(high_sem_struct_high / high_sem_count) if high_sem_count > 0 else 0,
        "high_sem_lex_high_ratio": float(high_sem_lex_high / high_sem_count) if high_sem_count > 0 else 0,
    }


def diagnose_issue(corr_data: Dict, struct_stats: Dict, lex_stats: Dict, sem_stats: Dict) -> Dict:
    """
    诊断问题根源。
    
    Returns:
        Dict with diagnosis results and recommendations
    """
    diagnosis = {
        "likely_issue": "unknown",
        "confidence": "low",
        "evidence": [],
        "recommendations": [],
    }
    
    # 检查 1: 语义耦合是否缺乏区分度
    sem_std = sem_stats.get("sem_std", 0)
    sem_mean = sem_stats.get("sem_mean", 0)
    
    if sem_std < 0.05 and sem_mean > 0.9:
        diagnosis["likely_issue"] = "tool_issue"
        diagnosis["confidence"] = "high"
        diagnosis["evidence"].append(
            f"语义耦合标准差极低 ({sem_std:.4f})，平均值极高 ({sem_mean:.4f})，"
            "说明所有模块对的语义相似度都很接近，缺乏区分度"
        )
        diagnosis["recommendations"].append(
            "改进文本提取：增加更多语义信息（Javadoc、注释、方法体摘要等）"
        )
        diagnosis["recommendations"].append(
            "尝试其他模型：CodeBERT 可能不适合这种粒度的分析"
        )
        return diagnosis
    
    # 检查 2: 语义耦合与结构/词汇耦合的相关性
    struct_sem_corr = corr_data["struct_sem_correlation"]
    lex_sem_corr = corr_data["lex_sem_correlation"]
    
    if struct_sem_corr < 0.1 and lex_sem_corr < 0.1:
        diagnosis["likely_issue"] = "tool_issue"
        diagnosis["confidence"] = "medium"
        diagnosis["evidence"].append(
            f"语义耦合与结构耦合相关性极低 ({struct_sem_corr:.4f})，"
            f"与词汇耦合相关性也极低 ({lex_sem_corr:.4f})"
        )
        diagnosis["evidence"].append(
            "正常情况下，语义相关的模块在结构和词汇上也应该相关"
        )
        diagnosis["recommendations"].append(
            "检查文本提取质量：可能提取的文本信息不足或质量差"
        )
        return diagnosis
    
    # 检查 3: 高语义耦合的模块对是否在结构/词汇上也高耦合
    high_sem_struct_ratio = corr_data["high_sem_struct_high_ratio"]
    high_sem_lex_ratio = corr_data["high_sem_lex_high_ratio"]
    
    if high_sem_struct_ratio < 0.1 and high_sem_lex_ratio < 0.1:
        diagnosis["likely_issue"] = "tool_issue"
        diagnosis["confidence"] = "medium"
        diagnosis["evidence"].append(
            f"高语义耦合的模块对中，只有 {high_sem_struct_ratio*100:.1f}% 在结构上高耦合，"
            f"只有 {high_sem_lex_ratio*100:.1f}% 在词汇上高耦合"
        )
        diagnosis["evidence"].append(
            "如果代码质量正常，语义相似的模块应该在结构和词汇上也相似"
        )
        diagnosis["recommendations"].append(
            "改进文本提取或尝试其他模型"
        )
        return diagnosis
    
    # 检查 4: 如果三种耦合都高，可能是代码质量问题
    struct_mean = struct_stats.get("struct_mean", 0)
    lex_mean = lex_stats.get("lex_mean", 0)
    sem_mean = sem_stats.get("sem_mean", 0)
    
    if struct_mean > 0.1 and lex_mean > 0.1 and sem_mean > 0.5:
        diagnosis["likely_issue"] = "code_quality"
        diagnosis["confidence"] = "medium"
        diagnosis["evidence"].append(
            f"三种耦合度都较高：结构 {struct_mean:.4f}，词汇 {lex_mean:.4f}，语义 {sem_mean:.4f}"
        )
        diagnosis["evidence"].append(
            "可能存在的代码质量问题："
        )
        diagnosis["recommendations"].append(
            "检查代码重复度：可能存在大量重复代码"
        )
        diagnosis["recommendations"].append(
            "检查类的职责：可能很多类做类似的事情，缺少清晰的领域边界"
        )
        diagnosis["recommendations"].append(
            "检查命名规范：可能命名过于相似，导致词汇耦合高"
        )
        diagnosis["recommendations"].append(
            "考虑重构：提取公共抽象、减少重复、明确职责边界"
        )
        return diagnosis
    
    # 检查 5: 如果结构耦合低但语义耦合高，更可能是工具问题
    if struct_mean < 0.01 and sem_mean > 0.9:
        diagnosis["likely_issue"] = "tool_issue"
        diagnosis["confidence"] = "high"
        diagnosis["evidence"].append(
            f"结构耦合极低 ({struct_mean:.4f})，但语义耦合极高 ({sem_mean:.4f})"
        )
        diagnosis["evidence"].append(
            "如果代码结构清晰（低结构耦合），语义耦合不应该这么高"
        )
        diagnosis["recommendations"].append(
            "这是典型的工具问题：文本提取不足或模型不适合"
        )
        return diagnosis
    
    # 默认：可能是混合问题
    diagnosis["likely_issue"] = "mixed"
    diagnosis["confidence"] = "low"
    diagnosis["evidence"].append("需要进一步分析")
    diagnosis["recommendations"].append("检查具体的高耦合模块对，判断是工具问题还是代码问题")
    
    return diagnosis


def print_diagnosis(corr_data: Dict, struct_stats: Dict, lex_stats: Dict, sem_stats: Dict, diagnosis: Dict):
    """打印诊断结果。"""
    print("\n" + "=" * 70)
    print("代码质量 vs 工具问题诊断")
    print("=" * 70)
    
    print("\n【耦合度统计】")
    print(f"结构耦合: 平均 {struct_stats['struct_mean']:.6f}, "
          f"中位数 {struct_stats['struct_median']:.6f}, "
          f"标准差 {struct_stats['struct_std']:.6f}")
    print(f"词汇耦合: 平均 {lex_stats['lex_mean']:.6f}, "
          f"中位数 {lex_stats['lex_median']:.6f}, "
          f"标准差 {lex_stats['lex_std']:.6f}")
    print(f"语义耦合: 平均 {sem_stats['sem_mean']:.6f}, "
          f"中位数 {sem_stats['sem_median']:.6f}, "
          f"标准差 {sem_stats['sem_std']:.6f}")
    
    print("\n【耦合类型相关性】")
    print(f"结构 ↔ 词汇: {corr_data['struct_lex_correlation']:.4f}")
    print(f"结构 ↔ 语义: {corr_data['struct_sem_correlation']:.4f}")
    print(f"词汇 ↔ 语义: {corr_data['lex_sem_correlation']:.4f}")
    
    print(f"\n【高语义耦合分析】")
    print(f"高语义耦合对 (>0.9): {corr_data['high_sem_count']:,}")
    if corr_data['high_sem_count'] > 0:
        print(f"  其中结构耦合平均值: {corr_data['high_sem_struct_mean']:.6f}")
        print(f"  其中词汇耦合平均值: {corr_data['high_sem_lex_mean']:.6f}")
        print(f"  其中结构高耦合比例: {corr_data['high_sem_struct_high_ratio']*100:.1f}%")
        print(f"  其中词汇高耦合比例: {corr_data['high_sem_lex_high_ratio']*100:.1f}%")
    
    print("\n" + "=" * 70)
    print("诊断结果")
    print("=" * 70)
    print(f"\n可能的问题: {diagnosis['likely_issue']}")
    print(f"置信度: {diagnosis['confidence']}")
    
    print("\n证据:")
    for i, evidence in enumerate(diagnosis['evidence'], 1):
        print(f"  {i}. {evidence}")
    
    print("\n建议:")
    for i, rec in enumerate(diagnosis['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diagnose whether high semantic coupling is a tool issue or code quality issue"
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
    
    print(f"Loading matrices from: {base_dir}")
    
    struct_path = base_dir / f"{base_name}_S_struct.csv"
    lex_path = base_dir / f"{base_name}_S_lex.csv"
    sem_path = base_dir / f"{base_name}_S_sem.csv"
    
    modules, struct_matrix = load_matrix_csv(str(struct_path))
    _, lex_matrix = load_matrix_csv(str(lex_path))
    _, sem_matrix = load_matrix_csv(str(sem_path))
    
    print(f"Analyzing {len(modules)} modules...")
    
    # 计算统计信息
    n = len(modules)
    off_diag_mask = ~np.eye(n, dtype=bool)
    
    def calc_stats(arr, name):
        arr_off = arr[off_diag_mask]
        return {
            f"{name}_mean": float(np.mean(arr_off)),
            f"{name}_median": float(np.median(arr_off)),
            f"{name}_std": float(np.std(arr_off)),
        }
    
    struct_stats = calc_stats(struct_matrix, "struct")
    lex_stats = calc_stats(lex_matrix, "lex")
    sem_stats = calc_stats(sem_matrix, "sem")
    
    # 分析相关性
    corr_data = analyze_coupling_correlation(struct_matrix, lex_matrix, sem_matrix)
    
    # 诊断
    diagnosis = diagnose_issue(corr_data, struct_stats, lex_stats, sem_stats)
    
    # 打印结果
    print_diagnosis(corr_data, struct_stats, lex_stats, sem_stats, diagnosis)


if __name__ == "__main__":
    main()

