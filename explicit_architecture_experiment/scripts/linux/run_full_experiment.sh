#!/bin/bash
# 完整实验流程脚本

set -e

echo "🚀 开始显性架构完整实验流程..."

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <source_project_dir> [output_dir]"
    echo "示例: $0 ./sample_projects ./experiment_results"
    exit 1
fi

SOURCE_DIR=$1
OUTPUT_DIR=${2:-"./experiment_results"}

echo "📂 源代码目录: $SOURCE_DIR"
echo "📁 输出目录: $OUTPUT_DIR"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 1. 数据生成
echo "📊 步骤 1: 数据生成..."
./run_data_generation.sh "$SOURCE_DIR" "$OUTPUT_DIR/dataset"

# 2. 模型训练
echo "🤖 步骤 2: 模型训练..."
./run_training.sh \
    "$OUTPUT_DIR/dataset/explicit_samples.json" \
    "$OUTPUT_DIR/dataset/non_explicit_samples.json" \
    "gpt2" \
    "$OUTPUT_DIR/models"

# 3. 评估分析
echo "📈 步骤 3: 评估分析..."
./run_evaluation.sh \
    "$OUTPUT_DIR/models/explicit_model" \
    "$OUTPUT_DIR/models/implicit_model" \
    "$OUTPUT_DIR/dataset/test.json" \
    "$OUTPUT_DIR/evaluation"

# 4. 生成分析报告
echo "📋 步骤 4: 生成分析报告..."
python ../../analysis/generate_report.py \
    --explicit_eval "$OUTPUT_DIR/evaluation/explicit_evaluation.jsonl" \
    --implicit_eval "$OUTPUT_DIR/evaluation/implicit_evaluation.jsonl" \
    --coupling_report "$OUTPUT_DIR/dataset/coupling_report.csv" \
    --attention_analysis "$OUTPUT_DIR/evaluation/attention_analysis" \
    --probe_analysis "$OUTPUT_DIR/evaluation/probe_analysis" \
    --output "$OUTPUT_DIR/final_report.json"

echo "✅ 完整实验流程完成!"
echo "📊 最终结果:"
echo "   - 数据集: $OUTPUT_DIR/dataset/"
echo "   - 模型: $OUTPUT_DIR/models/"
echo "   - 评估: $OUTPUT_DIR/evaluation/"
echo "   - 最终报告: $OUTPUT_DIR/final_report.json"
echo ""
echo "🎯 实验总结:"
echo "   显性架构实验已完成，请查看最终报告了解详细结果。"
