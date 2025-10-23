#!/bin/bash
# 数据生成脚本

set -e

echo "🚀 开始显性架构实验数据生成..."

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <source_project_dir> [output_dir]"
    echo "示例: $0 ./sample_projects ./dataset_out"
    exit 1
fi

SOURCE_DIR=$1
OUTPUT_DIR=${2:-"./dataset_out"}

echo "📂 源代码目录: $SOURCE_DIR"
echo "📁 输出目录: $OUTPUT_DIR"

# 检查源代码目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ 错误: 源代码目录不存在: $SOURCE_DIR"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 运行数据生成脚本
echo "🔧 运行数据生成脚本..."
python ../../data_generation/data_builder.py \
    --src "$SOURCE_DIR" \
    --out "$OUTPUT_DIR"

# 运行耦合度分析
echo "🔍 运行耦合度分析..."
python ../../data_generation/coupling_analyzer.py \
    --explicit_dir "$OUTPUT_DIR/explicit_view" \
    --implicit_dir "$OUTPUT_DIR/non_explicit_view" \
    --output_dir "$OUTPUT_DIR/coupling_analysis"

echo "✅ 数据生成完成!"
echo "📊 输出文件:"
echo "   - 显性架构样本: $OUTPUT_DIR/explicit_samples.json"
echo "   - 非显性架构样本: $OUTPUT_DIR/non_explicit_samples.json"
echo "   - 耦合度报告: $OUTPUT_DIR/coupling_report.csv"
echo "   - 耦合度对比图: $OUTPUT_DIR/coupling_comparison.png"
