#!/bin/bash
# 模型训练脚本

set -e

echo "🚀 开始显性架构实验模型训练..."

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法: $0 <explicit_data> <implicit_data> [model_name] [output_dir]"
    echo "示例: $0 ./dataset_out/explicit_samples.json ./dataset_out/non_explicit_samples.json gpt2 ./outputs"
    exit 1
fi

EXPLICIT_DATA=$1
IMPLICIT_DATA=$2
MODEL_NAME=${3:-"gpt2"}
OUTPUT_DIR=${4:-"./outputs"}

echo "📊 显性架构数据: $EXPLICIT_DATA"
echo "📊 非显性架构数据: $IMPLICIT_DATA"
echo "🤖 模型名称: $MODEL_NAME"
echo "📁 输出目录: $OUTPUT_DIR"

# 检查数据文件是否存在
if [ ! -f "$EXPLICIT_DATA" ]; then
    echo "❌ 错误: 显性架构数据文件不存在: $EXPLICIT_DATA"
    exit 1
fi

if [ ! -f "$IMPLICIT_DATA" ]; then
    echo "❌ 错误: 非显性架构数据文件不存在: $IMPLICIT_DATA"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 训练显性架构模型
echo "🔧 训练显性架构模型..."
python ../../training/finetune.py \
    --model_name "$MODEL_NAME" \
    --output_dir "$OUTPUT_DIR/explicit_model" \
    --train_file "$EXPLICIT_DATA" \
    --val_file "$EXPLICIT_DATA" \
    --epochs 3 \
    --batch_size 4 \
    --learning_rate 5e-5

# 训练非显性架构模型
echo "🔧 训练非显性架构模型..."
python ../../training/finetune.py \
    --model_name "$MODEL_NAME" \
    --output_dir "$OUTPUT_DIR/implicit_model" \
    --train_file "$IMPLICIT_DATA" \
    --val_file "$IMPLICIT_DATA" \
    --epochs 3 \
    --batch_size 4 \
    --learning_rate 5e-5

echo "✅ 模型训练完成!"
echo "📊 输出模型:"
echo "   - 显性架构模型: $OUTPUT_DIR/explicit_model"
echo "   - 非显性架构模型: $OUTPUT_DIR/implicit_model"
