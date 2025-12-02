import argparse

from .combine import compute_semantic_coupling
from .io import load_modules_from_json, save_sc_matrices
from .sem_coupling import compute_embeddings_inplace


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute semantic coupling matrices from module JSON",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件，包含模块列表、结构依赖与可选 embedding",
    )
    parser.add_argument(
        "--out-prefix",
        required=True,
        help="输出文件前缀，例如: out/my_project",
    )
    parser.add_argument("--alpha", type=float, default=0.4)
    parser.add_argument("--beta", type=float, default=0.2)
    parser.add_argument("--gamma", type=float, default=0.4)
    parser.add_argument(
        "--embed-model",
        type=str,
        default=None,
        help=(
            "可选：sentence-transformers 模型名。"
            "若提供，则在 Python 侧自动为每个模块计算 embedding。"
            "例如: microsoft/codebert-base"
        ),
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="可选：embedding 计算所用设备，例如 'cuda' 或 'cpu'。默认由 sentence-transformers 决定。",
    )
    parser.add_argument(
        "--model-cache-dir",
        type=str,
        default=None,
        help="可选：模型缓存目录。如果提供，会保存模型到该目录，下次运行时直接加载，避免重复下载。",
    )

    args = parser.parse_args()

    modules, edge_w = load_modules_from_json(args.input)

    if args.embed_model:
        compute_embeddings_inplace(
            modules,
            model_name=args.embed_model,
            device=args.device,
            cache_dir=args.model_cache_dir,
        )

    sc = compute_semantic_coupling(
        modules,
        edge_type_weights=edge_w,
        alpha=args.alpha,
        beta=args.beta,
        gamma=args.gamma,
    )

    save_sc_matrices(args.out_prefix, sc)


if __name__ == "__main__":
    main()


