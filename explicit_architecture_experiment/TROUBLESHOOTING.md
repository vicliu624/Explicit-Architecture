# 故障排除指南

## 常见安装问题

### 1. Python环境问题

#### 问题：`python` 命令不存在
**解决方案：**
```bash
# Windows: 检查Python是否添加到PATH
# 重新安装Python并勾选"Add Python to PATH"

# Linux/macOS: 使用python3
python3 --version
# 或者创建别名
alias python=python3
```

#### 问题：Python版本过低
**解决方案：**
```bash
# 检查版本
python --version

# 升级到Python 3.8+
# Windows: 从官网下载最新版本
# Linux: sudo apt update && sudo apt install python3.9
# macOS: brew install python@3.9
```

### 2. 包安装失败

#### 问题：pip安装超时
**解决方案：**
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或者使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

#### 问题：权限错误
**解决方案：**
```bash
# 使用用户安装
pip install --user -r requirements.txt

# 或者使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### 问题：依赖冲突
**解决方案：**
```bash
# 清理pip缓存
pip cache purge

# 重新安装
pip install --no-cache-dir -r requirements.txt

# 或者使用最小依赖
pip install -r requirements-minimal.txt
```

### 3. 特定包问题

#### PyTorch安装问题
**解决方案：**
```bash
# 访问PyTorch官网获取正确命令
# https://pytorch.org/get-started/locally/

# CPU版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# CUDA版本（根据你的CUDA版本选择）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### tree-sitter安装问题
**解决方案：**
```bash
# Windows: 安装Visual Studio Build Tools
# 下载地址: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Linux: 安装编译工具
sudo apt-get update
sudo apt-get install build-essential

# macOS: 安装Xcode命令行工具
xcode-select --install

# 然后重新安装
pip install tree-sitter tree-sitter-languages
```

#### transformers安装问题
**解决方案：**
```bash
# 如果安装失败，尝试指定版本
pip install transformers==4.35.0

# 或者从源码安装
pip install git+https://github.com/huggingface/transformers.git
```

### 4. 运行时错误

#### 问题：`ModuleNotFoundError`
**解决方案：**
```bash
# 检查虚拟环境是否激活
which python  # Linux/macOS
where python  # Windows

# 重新激活环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 检查包是否安装
pip list | grep package_name
```

#### 问题：CUDA相关错误
**解决方案：**
```bash
# 检查CUDA是否可用
python -c "import torch; print(torch.cuda.is_available())"

# 如果不可用，使用CPU版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### 问题：内存不足
**解决方案：**
```bash
# 减少批处理大小
# 在训练脚本中修改batch_size参数

# 使用梯度累积
# 在训练脚本中增加gradient_accumulation_steps

# 使用更小的模型
# 将gpt2改为gpt2-small或使用其他小模型
```

### 5. 脚本执行问题

#### Windows PowerShell执行策略问题
**解决方案：**
```powershell
# 设置执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或者直接运行
PowerShell -ExecutionPolicy Bypass -File .\scripts\windows\run_data_generation.ps1
```

#### 路径问题
**解决方案：**
```bash
# 确保在正确的目录下运行
cd explicit_architecture_experiment

# 使用绝对路径
python C:\path\to\explicit_architecture_experiment\data_generation\data_builder.py

# 检查路径中是否包含空格或特殊字符
```

### 6. 数据问题

#### 问题：找不到源代码文件
**解决方案：**
```bash
# 检查目录结构
ls -la source_project_dir/

# 确保包含支持的源代码文件
# 支持: .py, .java, .js, .ts, .cpp, .c, .cs, .go, .rs

# 检查文件权限
chmod -R 755 source_project_dir/
```

#### 问题：代码解析失败
**解决方案：**
```bash
# 检查文件编码
file source_file.java

# 确保文件是UTF-8编码
# 如果编码有问题，转换编码：
iconv -f GBK -t UTF-8 source_file.java > source_file_utf8.java
```

### 7. 性能优化

#### 问题：训练速度慢
**解决方案：**
```bash
# 使用GPU加速
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 减少数据量进行测试
# 在数据生成脚本中限制文件数量

# 使用更小的模型
# 修改训练脚本中的模型名称
```

#### 问题：内存占用过高
**解决方案：**
```bash
# 减少批处理大小
# 在训练配置中设置更小的batch_size

# 使用梯度检查点
# 在模型配置中启用gradient_checkpointing

# 清理不必要的变量
# 在代码中添加torch.cuda.empty_cache()
```

## 获取帮助

如果以上解决方案都不能解决问题：

1. **检查错误日志**：仔细阅读错误信息
2. **搜索解决方案**：在GitHub Issues或Stack Overflow搜索类似问题
3. **简化测试**：使用最小依赖包进行测试
4. **环境隔离**：创建全新的虚拟环境重新安装
5. **版本兼容性**：检查Python和包版本兼容性

## 测试环境

运行以下命令测试环境是否正常：

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 运行环境测试
python test_environment.py

# 如果测试通过，尝试运行简单示例
python -c "import torch; print('PyTorch版本:', torch.__version__)"
```

## 联系支持

如果问题仍然存在，请提供以下信息：

1. 操作系统版本
2. Python版本
3. 错误信息完整日志
4. 已尝试的解决方案
5. 环境测试脚本的输出
