# 显性架构实验：验证架构对代码理解和生成的影响

## 实验概述

本实验旨在验证**显性架构（Explicit Architecture）**相比**非显性架构（Non-Explicit Architecture）**在代码理解和生成任务中的优势。核心假设是：当代码的物理结构（目录/文件组织）与语义结构（模块边界）对齐时，能够降低函数间耦合度，提升模型的可预测性。

## 实验假设

### 主假设 (H1)
显性架构条件下，模型在代码生成/理解任务上比非显性架构表现更好。

### 机制假设 (H2)  
显性架构使得"语义边界"与"位置"更一致，模型的位置信号对语义类型/模块边界的可预测性更高。

## 实验设计

### 1. 数据构造
- **显性架构视图**：保持原有目录结构和文件命名，使路径含义明确
- **非显性架构视图**：打乱目录结构、随机文件命名，使语义与位置不对齐
- **关键控制**：保持代码内容完全相同，仅改变物理位置

### 2. 任务定义
- **函数补全任务**：掩盖函数体，预测实现
- **跨文件引用预测**：预测函数调用关系
- **耦合度分析**：计算import graph和call graph指标

### 3. 评估指标
- **性能指标**：Exact Match, CodeBLEU, AST相似度
- **耦合度指标**：fan_in, fan_out, import_in, import_out, coupling_score
- **机制分析**：注意力模式、线性探针、位置嵌入分析

## 文件结构

```
explicit_architecture_experiment/
├── README.md                           # 实验说明
├── EXPERIMENT_DESIGN.md               # 实验设计文档
├── requirements.txt                    # 依赖包
├── data_generation/                     # 数据生成模块
│   ├── data_builder.py                # 主数据构建脚本
│   └── coupling_analyzer.py           # 耦合度分析
├── training/                           # 训练模块
│   ├── finetune.py                    # 模型微调
│   └── configs/                       # 配置文件
│       └── finetune_config.json       # 训练配置
├── evaluation/                         # 评估模块
│   ├── eval_pipeline.py              # 评估流程
│   ├── attention_extractor.py        # 注意力提取
│   └── probe_trainer.py              # 线性探针训练
├── analysis/                          # 分析模块
│   ├── analysis_notebook.ipynb        # 分析notebook
│   └── generate_report.py            # 报告生成器
└── scripts/                           # 运行脚本
    ├── linux/                        # Linux脚本
    │   ├── run_data_generation.sh    # 数据生成
    │   ├── run_training.sh          # 模型训练
    │   ├── run_evaluation.sh        # 评估分析
    │   └── run_full_experiment.sh   # 完整实验流程
    └── windows/                      # Windows脚本
        ├── run_data_generation.bat   # 数据生成 (批处理)
        ├── run_training.bat         # 模型训练 (批处理)
        ├── run_evaluation.bat       # 评估分析 (批处理)
        ├── run_full_experiment.bat  # 完整实验流程 (批处理)
        ├── run_data_generation.ps1  # 数据生成 (PowerShell)
        ├── run_training.ps1         # 模型训练 (PowerShell)
        ├── run_evaluation.ps1       # 评估分析 (PowerShell)
        └── run_full_experiment.ps1  # 完整实验流程 (PowerShell)
```

## 快速开始

### 1. 环境安装

#### 方法一：使用快速安装脚本（推荐）

**Windows:**
```cmd
# 双击运行或在命令行执行
install.bat
```

**Linux/macOS:**
```bash
# 给脚本执行权限并运行
chmod +x install.sh
./install.sh
```

#### 方法二：手动安装

1. **创建虚拟环境**
```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

2. **安装依赖**
```bash
# 升级pip
python -m pip install --upgrade pip

# 安装PyTorch
pip install torch torchvision torchaudio

# 安装其他依赖
pip install -r requirements.txt
```

3. **验证安装**
```bash
python test_environment.py
```

#### 详细安装指南
查看 [SETUP.md](SETUP.md) 获取完整的安装说明和故障排除指南。

### 2. 准备源代码项目
   - 将你的Java/Python/JavaScript等项目放在一个目录中
   - 支持的语言：Python, Java, JavaScript, TypeScript, C++, C#, C, Go, Rust

### 3. 运行实验

**Linux/macOS:**
```bash
bash scripts/linux/run_data_generation.sh <source_project_dir>
```

**Windows (批处理):**
```cmd
scripts\windows\run_data_generation.bat <source_project_dir>
```

**Windows (PowerShell):**
```powershell
.\scripts\windows\run_data_generation.ps1 -SourceDir <source_project_dir>
```

4. **训练模型**

**Linux/macOS:**
```bash
bash scripts/linux/run_training.sh <explicit_data> <implicit_data>
```

**Windows (批处理):**
```cmd
scripts\windows\run_training.bat <explicit_data> <implicit_data>
```

**Windows (PowerShell):**
```powershell
.\scripts\windows\run_training.ps1 -ExplicitData <explicit_data> -ImplicitData <implicit_data>
```

5. **评估分析**

**Linux/macOS:**
```bash
bash scripts/linux/run_evaluation.sh <explicit_model> <implicit_model> <test_data>
```

**Windows (批处理):**
```cmd
scripts\windows\run_evaluation.bat <explicit_model> <implicit_model> <test_data>
```

**Windows (PowerShell):**
```powershell
.\scripts\windows\run_evaluation.ps1 -ExplicitModel <explicit_model> -ImplicitModel <implicit_model> -TestData <test_data>
```

6. **完整实验流程**

**Linux/macOS:**
```bash
bash scripts/linux/run_full_experiment.sh <source_project_dir>
```

**Windows (批处理):**
```cmd
scripts\windows\run_full_experiment.bat <source_project_dir>
```

**Windows (PowerShell):**
```powershell
.\scripts\windows\run_full_experiment.ps1 -SourceDir <source_project_dir>
```

## 预期结果

- 显性架构在函数补全任务上显著优于非显性架构
- 显性架构的耦合度指标更低
- 显性架构的注意力模式更集中，位置信号更可预测
- 线性探针在显性架构下分类准确率更高

## 贡献

本实验为理解代码架构对AI模型性能的影响提供了量化证据，对软件工程和AI系统设计具有重要价值。
