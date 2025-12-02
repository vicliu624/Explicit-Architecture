"""
检查 project_modules.json 中模块文本内容的工具。

用于诊断语义耦合度异常高的问题。
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict


def inspect_module_texts(json_path: str, num_samples: int = 10) -> None:
    """检查模块文本内容。"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    modules = data.get("modules", [])
    
    if not modules:
        print("No modules found in JSON file")
        return
    
    print(f"Total modules: {len(modules)}")
    print(f"\n{'='*70}")
    print("Sample Module Texts (first {} modules)".format(num_samples))
    print("="*70)
    
    for i, module in enumerate(modules[:num_samples], 1):
        module_id = module.get("id", "unknown")
        text = module.get("text", "")
        text_length = len(text)
        text_preview = text[:200] + "..." if len(text) > 200 else text
        
        print(f"\n[{i}] {module_id}")
        print(f"    Text length: {text_length} chars")
        print(f"    Text preview: {text_preview}")
        
        # 分析文本内容
        words = text.split()
        unique_words = len(set(words))
        print(f"    Word count: {len(words)} | Unique words: {unique_words}")
        
        # 检查是否包含 Javadoc
        has_javadoc = "/**" in text or "*" in text[:50]
        print(f"    Has Javadoc: {has_javadoc}")
    
    # 统计所有模块的文本长度
    text_lengths = [len(m.get("text", "")) for m in modules]
    avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
    min_length = min(text_lengths) if text_lengths else 0
    max_length = max(text_lengths) if text_lengths else 0
    
    print(f"\n{'='*70}")
    print("Text Length Statistics")
    print("="*70)
    print(f"Average: {avg_length:.1f} chars")
    print(f"Min: {min_length} chars")
    print(f"Max: {max_length} chars")
    
    # 检查空文本或过短文本
    empty_count = sum(1 for l in text_lengths if l == 0)
    short_count = sum(1 for l in text_lengths if 0 < l < 50)
    
    print(f"\nEmpty texts: {empty_count} ({empty_count/len(modules)*100:.1f}%)")
    print(f"Short texts (<50 chars): {short_count} ({short_count/len(modules)*100:.1f}%)")
    
    # 检查 Javadoc 覆盖率
    javadoc_count = sum(1 for m in modules if "/**" in m.get("text", "") or "*" in m.get("text", "")[:50])
    print(f"Modules with Javadoc: {javadoc_count} ({javadoc_count/len(modules)*100:.1f}%)")


def compare_module_texts(json_path: str, module_id1: str, module_id2: str) -> None:
    """对比两个模块的文本内容。"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    modules = {m["id"]: m for m in data.get("modules", [])}
    
    if module_id1 not in modules:
        print(f"Module not found: {module_id1}")
        return
    if module_id2 not in modules:
        print(f"Module not found: {module_id2}")
        return
    
    m1 = modules[module_id1]
    m2 = modules[module_id2]
    
    print(f"\n{'='*70}")
    print("Module Text Comparison")
    print("="*70)
    
    print(f"\n[1] {module_id1}")
    print(f"    Text: {m1.get('text', '')}")
    
    print(f"\n[2] {module_id2}")
    print(f"    Text: {m2.get('text', '')}")
    
    # 计算词汇重叠
    words1 = set(m1.get("text", "").split())
    words2 = set(m2.get("text", "").split())
    overlap = words1 & words2
    union = words1 | words2
    
    if union:
        jaccard = len(overlap) / len(union)
        print(f"\nJaccard similarity: {jaccard:.4f}")
        print(f"Overlapping words: {len(overlap)}")
        print(f"Common words: {sorted(list(overlap))[:20]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect module text content in project_modules.json"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to project_modules.json",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10,
        help="Number of sample modules to show (default: 10)",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("MODULE1", "MODULE2"),
        help="Compare text content of two modules",
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_module_texts(args.input, args.compare[0], args.compare[1])
    else:
        inspect_module_texts(args.input, args.samples)


if __name__ == "__main__":
    main()

