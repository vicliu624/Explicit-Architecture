# 语义耦合度（Semantic Coupling）分析工具

本工具包实现了从 Java 工程源码到语义耦合度矩阵的完整分析流程，支持：
- **结构耦合** (S_struct)：基于静态依赖关系（调用、继承、字段、静态导入）
- **词汇耦合** (S_lex)：基于 TF-IDF 的词汇相似度
- **语义耦合** (S_sem)：基于 CodeBERT 的语义相似度
- **综合耦合** (SC)：上述三种耦合度的加权组合

## 目录结构

```
semantic_coupling/
├── README.md                  # 本文档
├── TROUBLESHOOTING.md         # 故障排除指南
├── __init__.py                # 包初始化
├── models.py                  # 数据模型定义
├── io.py                      # JSON/CSV 读写
├── struct_coupling.py         # 结构耦合计算
├── lex_coupling.py            # 词汇耦合计算
├── sem_coupling.py            # 语义耦合计算
├── combine.py                 # 综合耦合计算
├── cli_compute_sc.py          # 命令行计算工具
├── analyze_sc.py              # 结果分析工具
├── evaluate_coupling.py       # 综合健康度评估工具
├── inspect_text.py            # 模块文本内容检查工具
└── diagnose_code_quality.py   # 代码质量 vs 工具问题诊断工具

../java_extractor/             # Java 源码抽取器（Maven 项目）
```

## 快速开始

### 1. 环境准备

#### Python 环境

```bash
# 创建 conda 环境（推荐）
conda create -n explicit-arch python=3.10 -y
conda activate explicit-arch

# 安装依赖
cd explicit_architecture_experiment
pip install -r requirements-minimal-ascii.txt
pip install sentence-transformers pandas
```

#### Java 环境

确保已安装：
- JDK 17+ 
- Maven 3.6+

### 2. 构建 Java 抽取器

```bash
cd java_extractor
mvn -q -DskipTests package
```

成功后会在 `target/` 目录生成：
- `java-extractor-0.1.0-SNAPSHOT-jar-with-dependencies.jar`

### 3. 从 Java 工程生成 `project_modules.json`

```bash
# Windows PowerShell
java -jar target/java-extractor-0.1.0-SNAPSHOT-jar-with-dependencies.jar `
  "C:\path\to\your-java-project\src\main\java" `
  "C:\path\to\your-java-project\project_modules.json"

# Linux/Mac
java -jar target/java-extractor-0.1.0-SNAPSHOT-jar-with-dependencies.jar \
  /path/to/your-java-project/src/main/java \
  /path/to/your-java-project/project_modules.json
```

**参数说明：**
- 第一个参数：Java 源码根目录（通常是 `src/main/java`）
- 第二个参数：输出的 `project_modules.json` 路径

**生成的 JSON 格式：**
```json
{
  "edge_type_weights": {
    "call": 1.0,
    "field": 0.8,
    "inherit": 0.9,
    "static_import": 0.6
  },
  "modules": [
    {
      "id": "com.example.user.UserService",
      "text": "UserService getUser createUser ... Javadoc ...",
      "deps": {
        "call": {"com.example.repo.UserRepo": 12},
        "inherit": {"com.example.base.BaseService": 1}
      }
    }
  ]
}
```

### 4. 计算语义耦合度矩阵

```bash
cd explicit_architecture_experiment

# 基本用法（只计算结构+词汇耦合，不计算语义向量）
python -m semantic_coupling.cli_compute_sc `
  --input "C:\path\to\project_modules.json" `
  --out-prefix "out\my_project"

# 完整用法（包含语义向量计算）
python -m semantic_coupling.cli_compute_sc `
  --input "C:\path\to\project_modules.json" `
  --out-prefix "out\my_project" `
  --embed-model microsoft/codebert-base `
  --device cpu `
  --model-cache-dir ".cache\models"
```

**参数说明：**
- `--input`: 输入的 `project_modules.json` 路径
- `--out-prefix`: 输出文件前缀（会生成 4 个 CSV 文件）
- `--embed-model`: 可选，用于计算语义向量的模型（如 `microsoft/codebert-base`）
- `--device`: 可选，`cpu` 或 `cuda`（默认自动选择）
- `--model-cache-dir`: 可选，模型缓存目录，避免重复下载
- `--alpha`, `--beta`, `--gamma`: 可选，综合耦合度的权重（默认 0.4, 0.2, 0.4）

**输出文件：**
- `{prefix}_S_struct.csv`: 结构耦合矩阵
- `{prefix}_S_lex.csv`: 词汇耦合矩阵
- `{prefix}_S_sem.csv`: 语义相似度矩阵（需要 `--embed-model`）
- `{prefix}_SC.csv`: 综合语义耦合矩阵

### 5. 分析结果

#### 查看统计信息

```bash
python -m semantic_coupling.analyze_sc `
  --matrix "out\my_project_SC.csv" `
  --stats-only
```

输出示例：
```
=== SC Matrix Statistics ===
Number of modules: 1224
Mean coupling: 0.023456
Median coupling: 0.012345
Std coupling: 0.045678
Max coupling: 0.923456
Min coupling: 0.000123
Strong ties (coupling > 0.5): 156
Weak ties (coupling < 0.1): 1234567
```

#### 提取 Top-K 强耦合模块对

```bash
python -m semantic_coupling.analyze_sc `
  --matrix "out\my_project_SC.csv" `
  --top-k 100 `
  --output "out\my_project_top100.csv"
```

**参数说明：**
- `--matrix`: 要分析的矩阵 CSV 文件
- `--top-k`: 提取前 K 个最强耦合对（默认 50）
- `--output`: 输出 CSV 路径（默认：`{matrix}_top{top_k}.csv`）
- `--stats-only`: 只显示统计信息，不导出 top-k

**导出的 CSV 格式：**
```csv
Rank,Module_A,Module_B,SC_Coupling
1,com.example.A,com.example.B,0.923456
2,com.example.C,com.example.D,0.891234
...
```

#### 综合健康度评估

评估项目的整体耦合健康度，对比三种耦合类型：

```bash
python -m semantic_coupling.evaluate_coupling `
  --prefix "out\my_project"
```

输出包括：
- 健康度评分（0-100）
- 三种耦合类型的详细统计
- 结构耦合与语义耦合的一致性分析
- 改进建议

#### 检查模块文本内容

如果语义耦合度异常高，检查提取的文本内容：

```bash
# 检查前 20 个模块的文本内容
python -m semantic_coupling.inspect_text `
  --input "C:\path\to\project_modules.json" `
  --samples 20

# 对比两个模块的文本
python -m semantic_coupling.inspect_text `
  --input "project_modules.json" `
  --compare "com.example.ClassA" "com.example.ClassB"
```

#### 诊断代码质量 vs 工具问题

判断语义耦合度高是工具问题还是代码质量问题：

```bash
python -m semantic_coupling.diagnose_code_quality `
  --prefix "out\my_project"
```

工具会分析：
- 三种耦合类型之间的相关性
- 高语义耦合模块对的特征
- 给出明确的诊断结论和改进建议

## 完整工作流示例

假设你要分析一个 Java 项目 `my-java-project`：

```bash
# 1. 构建 Java 抽取器（只需一次）
cd explicit_architecture_experiment/java_extractor
mvn -q -DskipTests package

# 2. 生成 project_modules.json
java -jar target/java-extractor-0.1.0-SNAPSHOT-jar-with-dependencies.jar `
  "C:\Projects\my-java-project\src\main\java" `
  "C:\Projects\my-java-project\project_modules.json"

# 3. 计算耦合矩阵
cd ..
mkdir -p out
python -m semantic_coupling.cli_compute_sc `
  --input "C:\Projects\my-java-project\project_modules.json" `
  --out-prefix "out\my-java-project" `
  --embed-model microsoft/codebert-base `
  --device cpu `
  --model-cache-dir ".cache\models"

# 4. 分析结果
python -m semantic_coupling.analyze_sc `
  --matrix "out\my-java-project_SC.csv" `
  --top-k 100

# 5. 综合健康度评估
python -m semantic_coupling.evaluate_coupling `
  --prefix "out\my-java-project"

# 6. 如果语义耦合度异常高，进行诊断
python -m semantic_coupling.diagnose_code_quality `
  --prefix "out\my-java-project"
python -m semantic_coupling.inspect_text `
  --input "C:\Projects\my-java-project\project_modules.json" `
  --samples 20
```

## 输出文件说明

### 矩阵 CSV 格式

所有矩阵 CSV 文件格式相同：
- 第一行：表头（空字符串 + 所有模块 ID）
- 后续行：`模块ID, 与其他模块的耦合度值...`

例如：
```csv
,com.example.A,com.example.B,com.example.C,...
com.example.A,1.0,0.5,0.3,...
com.example.B,0.5,1.0,0.8,...
...
```

### 矩阵类型说明

1. **S_struct (结构耦合)**
   - 基于静态依赖关系（调用、继承、字段、静态导入）
   - 值域：[0, 1]，值越大表示结构依赖越强

2. **S_lex (词汇耦合)**
   - 基于 TF-IDF + 余弦相似度
   - 值域：[0, 1]，值越大表示词汇相似度越高

3. **S_sem (语义耦合)**
   - 基于 CodeBERT 语义向量 + 余弦相似度
   - 值域：[0, 1]，值越大表示语义相似度越高

4. **SC (综合耦合)**
   - 公式：`SC = alpha * S_struct + beta * S_lex + gamma * S_sem`
   - 默认权重：alpha=0.4, beta=0.2, gamma=0.4
   - 值域：[0, 1]，综合反映模块间的耦合程度

## 常见问题

### Q: 为什么每次都要重新下载模型？

A: 使用 `--model-cache-dir` 参数指定缓存目录，模型会被保存到本地，下次直接加载：

```bash
--model-cache-dir ".cache\models"
```

### Q: 如何只计算结构+词汇耦合，不计算语义向量？

A: 不提供 `--embed-model` 参数即可。但注意：如果 JSON 中没有预先计算的 embedding，`S_sem` 会报错。可以修改 `combine.py` 让它在没有 embedding 时跳过语义耦合计算。

### Q: 支持其他语言吗？

A: 目前 `java_extractor` 只支持 Java。如果要支持其他语言，需要：
1. 实现对应的源码抽取器（生成相同格式的 `project_modules.json`）
2. Python 端的计算逻辑是通用的，无需修改

### Q: 如何处理大型项目（模块数 > 1000）？

A: 
- 语义向量计算会比较慢，建议使用 GPU（`--device cuda`）
- 可以先用 `--stats-only` 查看统计信息，再决定是否提取 top-k
- 矩阵 CSV 文件可能很大（几十 MB），建议用 `analyze_sc.py` 提取关键信息而不是直接打开

### Q: 如何自定义边类型权重？

A: 在 `project_modules.json` 中修改 `edge_type_weights` 字段，或在 Java 抽取器的 `Main.java` 中修改默认权重。

### Q: 语义耦合度异常高（接近 1.0）怎么办？

A: 这可能是工具问题或代码质量问题。使用诊断工具判断：

```bash
# 1. 诊断问题根源
python -m semantic_coupling.diagnose_code_quality `
  --prefix "out\my_project"

# 2. 检查文本提取质量
python -m semantic_coupling.inspect_text `
  --input "project_modules.json" `
  --samples 20
```

**如果是工具问题**（文本提取不足）：
- 使用改进后的 Java 抽取器重新生成 `project_modules.json`
- 或调整综合耦合度权重，降低语义耦合的影响

**如果是代码质量问题**（代码重复、职责不清）：
- 检查代码重复度
- 重构：提取公共抽象、明确职责边界
- 参考诊断工具的具体建议

详细说明见：`TROUBLESHOOTING.md`

## 诊断和故障排除

### 语义耦合度异常高的诊断流程

1. **运行诊断工具**
   ```bash
   python -m semantic_coupling.diagnose_code_quality `
     --prefix "out\my_project"
   ```

2. **检查文本内容**
   ```bash
   python -m semantic_coupling.inspect_text `
     --input "project_modules.json" `
     --samples 20
   ```

3. **根据诊断结果采取行动**
   - 工具问题 → 改进文本提取或调整权重
   - 代码质量问题 → 重构代码

详细故障排除指南见：`TROUBLESHOOTING.md`

## 技术细节

### 结构耦合计算

- 对每种边类型（call, field, inherit, static_import）赋予权重
- 统计模块 i 到模块 j 的加权边数
- 归一化到 [0, 1]

### 词汇耦合计算

- 使用 `sklearn.feature_extraction.text.TfidfVectorizer`
- 提取标识符（类名、方法名、字段名等）
- 计算文档间余弦相似度

### 语义耦合计算

- 使用 `sentence-transformers` 加载 CodeBERT 模型
- 将模块文本编码为向量
- 计算向量间余弦相似度并映射到 [0, 1]

## 参考

- 详细理论说明见：`../docs/一、目标（精炼）.md`
- 语义耦合度定义见：`../docs/语义耦合度.md`
- 故障排除指南见：`TROUBLESHOOTING.md`

