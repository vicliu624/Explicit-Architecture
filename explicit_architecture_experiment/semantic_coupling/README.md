# 语义耦合度（Semantic Coupling）分析工具

本工具包实现了**直接从 Transformer 内部机制提取语义耦合度指标**，不依赖 AST、调用图等传统中间表示。

## 核心思路

**新方法**：直接从 Transformer 的内部机制（attention、embedding、perplexity）提取指标，利用模型的语义捕捉能力量化源码各模块的语义耦合度。

### 技术路线

1. **直接读取源代码工程**：按文件/类划分模块
2. **Transformer 前向传播**：提取 attention 矩阵、token embedding、预测困惑度
3. **映射到模块粒度**：聚合得到模块间耦合矩阵
4. **生成语义耦合度矩阵**：可直接用于定量分析

### 提取的指标

1. **Attention 权重**
   - 模块内局部关注度 → 内部凝聚度
   - 跨模块关注度 → 模块间耦合度

2. **Token Embedding**
   - 模块内部 token 向量相似度 → 内部凝聚度
   - 模块间 token 向量相似度 → 模块间耦合

3. **层级表示差异**
   - 低层：语法结构耦合
   - 中层：函数/类调用模式耦合
   - 高层：模块级语义耦合

4. **预测困惑度**
   - 模块内部困惑度 → 内部一致性
   - 低困惑度 = 高一致性

## 目录结构

```
semantic_coupling/
├── README.md                      # 本文档
├── __init__.py                    # 包初始化
├── models.py                      # 数据模型（简化，新方法不需要复杂模型）
├── io.py                          # CSV 保存工具
├── transformer_metrics.py         # Transformer 指标提取核心逻辑
└── cli_compute_transformer_sc.py  # 命令行工具
```

## 快速开始

### 1. 环境准备

```bash
# 创建 conda 环境（推荐）
conda create -n explicit-arch python=3.10 -y
conda activate explicit-arch

# 安装依赖
cd explicit_architecture_experiment
pip install transformers torch scikit-learn numpy pandas
```

### 2. 直接分析源代码工程

```bash
# Windows PowerShell
python -m semantic_coupling.cli_compute_transformer_sc `
  --source-root "C:\path\to\your-java-project\src\main\java" `
  --out-prefix "out\transformer_sc" `
  --model microsoft/codebert-base `
  --device cpu `
  --metrics embedding,layer_wise

# Linux/Mac
python -m semantic_coupling.cli_compute_transformer_sc \
  --source-root /path/to/your-java-project/src/main/java \
  --out-prefix out/transformer_sc \
  --model microsoft/codebert-base \
  --device cpu \
  --metrics embedding,layer_wise
```

**参数说明：**
- `--source-root`: 源代码根目录（如 `src/main/java`）
- `--out-prefix`: 输出文件前缀
- `--model`: Transformer 模型名称（默认: `microsoft/codebert-base`）
- `--device`: 计算设备（`cpu` 或 `cuda`，默认自动选择）
- `--metrics`: 要计算的指标（`attention`, `embedding`, `perplexity`, `layer_wise`, `all`）
- `--file-extensions`: 文件扩展名，用逗号分隔（默认: `.java`）
- `--exclude`: 排除模式，用逗号分隔（默认: `test,__pycache__,.git,node_modules,target,build`）
- `--split-classes`: 是否按类分割 Java 文件（默认: False，整个文件作为一个模块）
- `--batch-size`: 批处理大小（默认: 8）
- `--max-length`: 最大序列长度（默认: 512）

### 3. 输出文件

- `{prefix}_embedding.csv`: Token embedding 相似度矩阵
- `{prefix}_low_layer.csv`: 低层（语法）耦合矩阵
- `{prefix}_mid_layer.csv`: 中层（调用模式）耦合矩阵
- `{prefix}_high_layer.csv`: 高层（模块语义）耦合矩阵

## 使用示例

### 基本用法

```bash
# 计算所有指标
python -m semantic_coupling.cli_compute_transformer_sc `
  --source-root "C:\Users\vicliu\Projects\YNII\ynjtgs-command-center\src\main\java" `
  --out-prefix "out\transformer_sc" `
  --model microsoft/codebert-base `
  --device cpu `
  --metrics all
```

### 只计算特定指标

```bash
# 只计算 embedding 和 layer-wise 耦合
python -m semantic_coupling.cli_compute_transformer_sc `
  --source-root "C:\path\to\project\src\main\java" `
  --out-prefix "out\transformer_sc" `
  --metrics embedding,layer_wise
```

### 按类分割 Java 文件

```bash
# 将每个 Java 类作为独立模块
python -m semantic_coupling.cli_compute_transformer_sc `
  --source-root "C:\path\to\project\src\main\java" `
  --out-prefix "out\transformer_sc" `
  --split-classes
```

### 支持多种语言

```bash
# 分析 Java、Python、JavaScript
python -m semantic_coupling.cli_compute_transformer_sc `
  --source-root "C:\path\to\project" `
  --out-prefix "out\transformer_sc" `
  --file-extensions ".java,.py,.js" `
  --exclude "test,__pycache__,.git,node_modules"
```

### 只提取高层表示（模块级语义）

```bash
# 只提取高层 Transformer 层的表示
python -m semantic_coupling.cli_compute_transformer_sc `
  --source-root "C:\path\to\project\src\main\java" `
  --out-prefix "out\transformer_sc" `
  --layers high
```

## 技术细节

### Attention 权重提取

- 从所有 Transformer 层提取 attention 矩阵
- 按层和 head 聚合得到模块间关注度
- **注意**：完整的 attention 分析需要 token 到模块的映射逻辑（待实现）

### Token Embedding

- 使用最后一层的 hidden states
- Mean pooling 得到模块级表示
- 余弦相似度计算模块间耦合

### 层级表示

- **低层**（前 1/3 层）：主要捕捉语法结构
- **中层**（中 1/3 层）：函数/类调用模式
- **高层**（后 1/3 层）：模块级语义

### 困惑度指标

- 仅支持 MLM 模型（如 CodeBERT）
- 计算每个模块的平均困惑度
- 低困惑度 = 高内部一致性

## 优势

1. **不依赖静态分析**：不需要 AST 解析器、调用图构建
2. **语义感知**：直接利用 Transformer 的语义理解能力
3. **多粒度分析**：不同层捕捉不同粒度的语义
4. **可解释性**：attention 权重可直接可视化

## 常见问题

### Q: 为什么不需要 Java 抽取器了？

A: 新方法直接从源代码提取，不需要 AST 解析和 JSON 中间文件。

### Q: 支持哪些模型？

A: 支持所有 HuggingFace Transformers 模型，推荐：
- `microsoft/codebert-base`（MLM，支持困惑度）
- `microsoft/graphcodebert-base`
- `Salesforce/codet5-base`

### Q: 如何选择指标？

A: 
- `embedding`: 最通用，适用于所有模型
- `layer_wise`: 提供多粒度分析
- `perplexity`: 仅 MLM 模型，提供内部一致性指标
- `attention`: 待完全实现

### Q: 输出矩阵如何分析？

A: 使用 Python 数据分析工具（pandas、numpy）或可视化工具（matplotlib、seaborn）分析生成的 CSV 矩阵。

## 与旧方法的区别

| 特性 | 旧方法 | 新方法 |
|------|--------|--------|
| 输入 | JSON 文件（需要 Java 抽取器） | 源代码目录 |
| 依赖 | AST、调用图 | Transformer 模型 |
| 指标来源 | 静态分析 + TF-IDF + Embedding | Transformer 内部机制 |
| 复杂度 | 高（多步骤） | 低（一步到位） |

## 未来计划

- [ ] 实现完整的 attention 分析（token 到模块映射）
- [ ] 支持跨文件 attention 分析
- [ ] 添加可视化工具
- [ ] 支持更多编程语言
