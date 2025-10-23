#!/bin/bash
# 评估分析脚本

set -e

echo "🚀 开始显性架构实验评估分析..."

# 检查参数
if [ $# -lt 3 ]; then
    echo "用法: $0 <explicit_model> <implicit_model> <test_data> [output_dir]"
    echo "示例: $0 ./outputs/explicit_model ./outputs/implicit_model ./dataset_out/test.json ./evaluation_out"
    exit 1
fi

EXPLICIT_MODEL=$1
IMPLICIT_MODEL=$2
TEST_DATA=$3
OUTPUT_DIR=${4:-"./evaluation_out"}

echo "🤖 显性架构模型: $EXPLICIT_MODEL"
echo "🤖 非显性架构模型: $IMPLICIT_MODEL"
echo "📊 测试数据: $TEST_DATA"
echo "📁 输出目录: $OUTPUT_DIR"

# 检查模型目录是否存在
if [ ! -d "$EXPLICIT_MODEL" ]; then
    echo "❌ 错误: 显性架构模型目录不存在: $EXPLICIT_MODEL"
    exit 1
fi

if [ ! -d "$IMPLICIT_MODEL" ]; then
    echo "❌ 错误: 非显性架构模型目录不存在: $IMPLICIT_MODEL"
    exit 1
fi

if [ ! -f "$TEST_DATA" ]; then
    echo "❌ 错误: 测试数据文件不存在: $TEST_DATA"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 评估显性架构模型
echo "📊 评估显性架构模型..."
python ../../evaluation/eval_pipeline.py \
    --model_dir "$EXPLICIT_MODEL" \
    --test_file "$TEST_DATA" \
    --output "$OUTPUT_DIR/explicit_evaluation.jsonl" \
    --max_new_tokens 256

# 评估非显性架构模型
echo "📊 评估非显性架构模型..."
python ../../evaluation/eval_pipeline.py \
    --model_dir "$IMPLICIT_MODEL" \
    --test_file "$TEST_DATA" \
    --output "$OUTPUT_DIR/implicit_evaluation.jsonl" \
    --max_new_tokens 256

# 提取注意力分析
echo "🔍 提取注意力分析..."
python ../../evaluation/attention_extractor.py \
    --model_dir "$EXPLICIT_MODEL" \
    --test_file "$TEST_DATA" \
    --output_dir "$OUTPUT_DIR/attention_analysis" \
    --max_length 512

# 训练线性探针
echo "🧪 训练线性探针..."
python ../../evaluation/probe_trainer.py \
    --model_dir "$EXPLICIT_MODEL" \
    --explicit_data "$TEST_DATA" \
    --implicit_data "$TEST_DATA" \
    --output_dir "$OUTPUT_DIR/probe_analysis"

echo "✅ 评估分析完成!"
echo "📊 输出文件:"
echo "   - 显性架构评估: $OUTPUT_DIR/explicit_evaluation.jsonl"
echo "   - 非显性架构评估: $OUTPUT_DIR/implicit_evaluation.jsonl"
echo "   - 注意力分析: $OUTPUT_DIR/attention_analysis/"
echo "   - 探针分析: $OUTPUT_DIR/probe_analysis/"
