#!/bin/bash
# Linux/macOS快速安装脚本

set -e

echo "🚀 开始安装显性架构实验环境..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3未安装"
    echo "请先安装Python 3.8+: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python已安装"
python3 --version

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "📈 升级pip..."
python -m pip install --upgrade pip

# 安装PyTorch
echo "🤖 安装PyTorch..."
pip install torch torchvision torchaudio

# 安装其他依赖
echo "📚 安装其他依赖包..."
pip install -r requirements.txt

# 验证安装
echo "🔍 验证安装..."
python -c "import torch, transformers, datasets, sklearn, networkx; print('✅ 所有核心包安装成功')"

echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 下一步："
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 准备你的Java项目数据"
echo "3. 运行实验: bash scripts/linux/run_full_experiment.sh ./your_java_project"
echo ""
