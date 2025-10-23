# Python环境安装指南

本指南将帮助你设置完整的Python环境来运行显性架构实验。

## 1. Python版本要求

- **Python 3.8+** (推荐 Python 3.9 或 3.10)
- 支持的操作系统：Windows, Linux, macOS

## 2. 环境设置方法

### 方法一：使用conda（推荐）

#### 2.1 安装Miniconda
```bash
# Windows: 下载并安装 Miniconda
# https://docs.conda.io/en/latest/miniconda.html

# Linux/macOS: 使用命令行安装
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

#### 2.2 创建虚拟环境
```bash
# 创建新的conda环境
conda create -n explicit_arch python=3.9

# 激活环境
conda activate explicit_arch

# Windows
conda activate explicit_arch

# Linux/macOS
source activate explicit_arch
```

#### 2.3 安装依赖
```bash
# 进入项目目录
cd explicit_architecture_experiment

# 安装PyTorch（根据你的系统选择）
# CPU版本
conda install pytorch torchvision torchaudio cpuonly -c pytorch

# GPU版本（如果有NVIDIA GPU）
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# 安装其他依赖
pip install -r requirements.txt
```

### 方法二：使用venv（Python内置）

#### 2.1 创建虚拟环境
```bash
# 进入项目目录
cd explicit_architecture_experiment

# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

#### 2.2 安装依赖
```bash
# 升级pip
python -m pip install --upgrade pip

# 安装PyTorch
pip install torch torchvision torchaudio

# 安装其他依赖
pip install -r requirements.txt
```

### 方法三：使用pipenv

#### 2.1 安装pipenv
```bash
pip install pipenv
```

#### 2.2 创建环境并安装依赖
```bash
# 进入项目目录
cd explicit_architecture_experiment

# 创建Pipfile并安装依赖
pipenv install

# 激活环境
pipenv shell
```

## 3. 验证安装

创建测试脚本验证环境：

```python
# test_environment.py
import sys
print(f"Python版本: {sys.version}")

try:
    import torch
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}")
except ImportError:
    print("❌ PyTorch未安装")

try:
    import transformers
    print(f"Transformers版本: {transformers.__version__}")
except ImportError:
    print("❌ Transformers未安装")

try:
    import datasets
    print(f"Datasets版本: {datasets.__version__}")
except ImportError:
    print("❌ Datasets未安装")

try:
    import sklearn
    print(f"Scikit-learn版本: {sklearn.__version__}")
except ImportError:
    print("❌ Scikit-learn未安装")

try:
    import networkx
    print(f"NetworkX版本: {networkx.__version__}")
except ImportError:
    print("❌ NetworkX未安装")

print("✅ 环境检查完成")
```

运行测试：
```bash
python test_environment.py
```

## 4. 常见问题解决

### 4.1 包安装失败

#### 问题：pip安装超时
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 问题：权限错误
```bash
# 使用用户安装
pip install --user -r requirements.txt
```

#### 问题：依赖冲突
```bash
# 清理缓存重新安装
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

### 4.2 特定包问题

#### tree-sitter安装问题
```bash
# 如果tree-sitter安装失败，先安装编译工具
# Windows: 安装Visual Studio Build Tools
# Linux: sudo apt-get install build-essential
# macOS: xcode-select --install

# 然后重新安装
pip install tree-sitter tree-sitter-languages
```

#### PyTorch安装问题
```bash
# 访问PyTorch官网获取正确的安装命令
# https://pytorch.org/get-started/locally/

# 例如，对于CUDA 11.8：
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4.3 内存不足
```bash
# 分批安装大包
pip install torch torchvision torchaudio
pip install transformers datasets
pip install scikit-learn numpy pandas
pip install matplotlib seaborn scipy
pip install tree-sitter networkx tqdm
```

## 5. 快速安装脚本

### Windows (PowerShell)
```powershell
# 创建快速安装脚本
@"
# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 升级pip
python -m pip install --upgrade pip

# 安装PyTorch
pip install torch torchvision torchaudio

# 安装其他依赖
pip install -r requirements.txt

# 验证安装
python -c "import torch, transformers, datasets; print('✅ 安装成功')"
"@ | Out-File -FilePath "install.ps1" -Encoding UTF8

# 运行安装脚本
.\install.ps1
```

### Linux/macOS (Bash)
```bash
#!/bin/bash
# 创建快速安装脚本

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 升级pip
python -m pip install --upgrade pip

# 安装PyTorch
pip install torch torchvision torchaudio

# 安装其他依赖
pip install -r requirements.txt

# 验证安装
python -c "import torch, transformers, datasets; print('✅ 安装成功')"
```

## 6. 环境管理最佳实践

### 6.1 环境隔离
- 为每个项目创建独立的虚拟环境
- 使用conda或venv管理依赖
- 定期更新requirements.txt

### 6.2 依赖管理
```bash
# 导出当前环境依赖
pip freeze > requirements.txt

# 安装特定版本
pip install package==1.2.3

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 6.3 环境备份
```bash
# 导出conda环境
conda env export > environment.yml

# 从文件创建环境
conda env create -f environment.yml
```

## 7. 下一步

环境安装完成后，你可以：

1. **运行测试脚本**验证安装
2. **准备数据**：将你的Java项目放在一个目录中
3. **开始实验**：使用相应的脚本运行实验

```bash
# 示例：运行完整实验
# Windows
.\scripts\windows\run_full_experiment.ps1 -SourceDir .\my_java_project

# Linux/macOS
bash scripts/linux/run_full_experiment.sh ./my_java_project
```

## 8. 获取帮助

如果遇到问题：

1. 检查Python版本是否符合要求
2. 确认虚拟环境已激活
3. 查看错误日志确定具体问题
4. 尝试使用不同的安装方法
5. 检查网络连接和镜像源设置

---

**注意**：首次安装可能需要较长时间，特别是PyTorch等大型包。建议使用稳定的网络连接。
