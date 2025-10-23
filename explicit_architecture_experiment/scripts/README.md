# 运行脚本说明

本目录包含用于运行显性架构实验的脚本，支持Linux/macOS和Windows平台。

## 目录结构

```
scripts/
├── linux/                    # Linux/macOS脚本
│   ├── run_data_generation.sh
│   ├── run_training.sh
│   ├── run_evaluation.sh
│   └── run_full_experiment.sh
└── windows/                  # Windows脚本
    ├── *.bat                 # 批处理脚本
    └── *.ps1                 # PowerShell脚本
```

## 平台选择

### Linux/macOS
使用 `linux/` 目录下的 `.sh` 脚本：
```bash
bash scripts/linux/run_data_generation.sh <source_project_dir>
```

### Windows
提供两种选择：

#### 1. 批处理脚本 (.bat)
适合传统Windows环境：
```cmd
scripts\windows\run_data_generation.bat <source_project_dir>
```

#### 2. PowerShell脚本 (.ps1)
更现代的选择，支持参数验证和错误处理：
```powershell
.\scripts\windows\run_data_generation.ps1 -SourceDir <source_project_dir>
```

## 脚本功能

### 1. 数据生成 (run_data_generation)
- 生成显性/非显性架构副本
- 创建函数补全任务样本
- 计算耦合度指标
- 输出训练/验证数据集

### 2. 模型训练 (run_training)
- 训练显性架构模型
- 训练非显性架构模型
- 使用相同的超参数确保公平比较

### 3. 评估分析 (run_evaluation)
- 评估两个模型的性能
- 提取注意力权重
- 训练线性探针
- 生成分析结果

### 4. 完整实验流程 (run_full_experiment)
- 自动执行上述所有步骤
- 生成最终实验报告
- 一键完成整个实验

## 使用示例

### 快速开始（推荐）
```bash
# Linux/macOS
bash scripts/linux/run_full_experiment.sh ./my_java_project

# Windows PowerShell
.\scripts\windows\run_full_experiment.ps1 -SourceDir .\my_java_project

# Windows 批处理
scripts\windows\run_full_experiment.bat .\my_java_project
```

### 分步执行
```bash
# 1. 数据生成
bash scripts/linux/run_data_generation.sh ./my_java_project

# 2. 模型训练
bash scripts/linux/run_training.sh ./dataset_out/explicit_samples.json ./dataset_out/non_explicit_samples.json

# 3. 评估分析
bash scripts/linux/run_evaluation.sh ./outputs/explicit_model ./outputs/implicit_model ./dataset_out/test.json
```

## 注意事项

1. **Python环境**：确保已安装所有依赖包
2. **路径分隔符**：Windows使用反斜杠 `\`，Linux/macOS使用正斜杠 `/`
3. **权限**：PowerShell脚本可能需要设置执行策略
4. **编码**：所有脚本使用UTF-8编码

## 故障排除

### Windows PowerShell执行策略
如果PowerShell脚本无法执行，请运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 路径问题
- 确保在项目根目录下运行脚本
- 使用相对路径或绝对路径
- 避免路径中包含空格或特殊字符

### 依赖问题
确保已安装所有Python依赖：
```bash
pip install -r requirements.txt
```
