# 语义耦合度分析 - 故障排除指南

## 问题：语义耦合度异常高（接近 1.0）

### 症状

- 语义耦合度（S_sem）的平均值接近 1.0（如 0.97+）
- 几乎所有模块对的语义相似度都很高
- 综合耦合度（SC）缺乏区分度，所有值都在 0.35-0.40 左右

### 诊断步骤

#### 1. 检查模块文本内容

使用 `inspect_text.py` 工具检查提取的文本：

```bash
python -m semantic_coupling.inspect_text `
  --input "C:\path\to\project_modules.json" `
  --samples 20
```

**检查要点：**
- 文本长度是否过短（< 50 字符）
- 是否包含 Javadoc 注释
- 文本内容是否过于简单（只有类名、方法名）

#### 2. 对比两个高耦合模块的文本

```bash
python -m semantic_coupling.inspect_text `
  --input "C:\path\to\project_modules.json" `
  --compare "com.example.ClassA" "com.example.ClassB"
```

查看它们的文本是否真的相似，还是提取的信息不足导致 CodeBERT 无法区分。

### 解决方案

#### 方案 1：使用改进的 Java 抽取器（推荐）

已改进的 `ProjectScanner.java` 会提取更丰富的语义信息：
- 字段类型信息
- 方法返回类型
- 完整的 Javadoc 注释（类级别、方法级别、字段级别）
- 行内注释

**重新生成 project_modules.json：**

```bash
cd java_extractor
mvn -q -DskipTests package

java -jar target/java-extractor-0.1.0-SNAPSHOT-jar-with-dependencies.jar `
  "C:\path\to\your-java-project\src\main\java" `
  "C:\path\to\your-java-project\project_modules.json"
```

然后重新计算耦合度矩阵。

#### 方案 2：调整综合耦合度权重

如果语义耦合确实缺乏区分度，降低其权重：

```bash
python -m semantic_coupling.cli_compute_sc `
  --input "project_modules.json" `
  --out-prefix "out\my_project" `
  --embed-model microsoft/codebert-base `
  --alpha 0.6 `
  --beta 0.3 `
  --gamma 0.1
```

这样结构耦合和词汇耦合的贡献会更大。

#### 方案 3：暂时忽略语义耦合

如果语义耦合完全无效，可以只用结构+词汇：

```bash
python -m semantic_coupling.cli_compute_sc `
  --input "project_modules.json" `
  --out-prefix "out\my_project" `
  --alpha 0.7 `
  --beta 0.3 `
  --gamma 0.0
```

注意：需要修改 `combine.py` 以支持 `gamma=0` 的情况，或者不提供 `--embed-model` 参数。

#### 方案 4：尝试其他模型

如果 CodeBERT 不适合，可以尝试：

1. **GraphCodeBERT**（如果可用）：
   ```bash
   --embed-model microsoft/graphcodebert-base
   ```

2. **其他代码模型**：
   - `microsoft/codebert-base-mlm`
   - `Salesforce/codet5-base`

3. **通用模型**（作为备选）：
   ```bash
   --embed-model sentence-transformers/all-MiniLM-L6-v2
   ```

### 预期结果

改进后，语义耦合度应该：
- 平均值在 0.1-0.5 之间（而不是 0.97+）
- 有明显的区分度（标准差 > 0.1）
- 存在弱耦合对（< 0.1）和强耦合对（> 0.5）

### 验证改进效果

运行综合评估工具：

```bash
python -m semantic_coupling.evaluate_coupling `
  --prefix "out\my_project"
```

检查：
1. 语义耦合的平均值是否降低
2. 标准差是否增大（说明有区分度）
3. 健康度评分是否提高

### 常见问题

**Q: 为什么改进后语义耦合度还是很高？**

A: 可能的原因：
1. 项目中的类确实语义相似（如大量相似的 DTO、Entity 类）
2. 代码注释不足，即使提取了所有信息，文本仍然相似
3. CodeBERT 模型本身对某些代码模式不敏感

**Q: 如何判断语义耦合是否有效？**

A: 检查：
1. 语义耦合与结构耦合的对比：如果两个模块结构上强耦合，语义上也应该强耦合
2. Top 10 语义耦合对是否合理：是否真的语义相关
3. 标准差：如果标准差很小（< 0.05），说明缺乏区分度

**Q: 可以完全依赖结构耦合和词汇耦合吗？**

A: 可以。如果语义耦合无效，结构耦合和词汇耦合已经能提供有价值的信息：
- 结构耦合反映实际的代码依赖
- 词汇耦合反映命名相似性（可能暗示设计模式或领域概念）

