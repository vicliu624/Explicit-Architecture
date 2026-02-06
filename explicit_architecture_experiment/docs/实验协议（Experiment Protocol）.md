从 Transformer 本身提取指标，而不是仅仅把 embedding 当作黑盒向量，然后计算相似度。目标是让 Transformer 直接输出可量化、可用于语义耦合度分析的指标。我们可以把技术路线拆解得更细：

1️⃣ Transformer 能直接提供哪些“可量化指标”

在处理源码的 Transformer 模型（如 CodeBERT、StarCoder、CodeLLaMA 等）时，它的输出不仅是 token 预测或 embedding，还可以衍生多种指标：

a. Attention 权重

每个 Transformer 层都会生成 self-attention 矩阵：

维度 [seq_len, seq_len]，表示每个 token 对其他 token 的关注度。

可量化指标：

类/函数内局部关注度：同一个模块内部 token 互相高关注 → 模块内耦合度高。

跨模块关注度：token 对不同文件或类的关注 → 模块间耦合度。

用法：

对 attention 矩阵做聚合（按 token 对应类/函数/模块分组），得到模块间耦合矩阵。

越高表示语义关联越强。

b. Token Embedding / Contextual Embedding

Transformer 的隐藏层输出 [seq_len, hidden_dim]，每个 token 一个向量。

可量化指标：

模块内部 token 向量平均相似度 → 内部凝聚度

模块间 token 向量相似度 → 模块间耦合

特点：

不依赖传统调用图，只依赖语义捕捉能力。

可用于量化语义耦合矩阵。

c. 层级表示差异

可以利用不同层的输出：

低层：主要捕捉语法结构

中层：函数/类调用模式

高层：模块级语义

指标用法：

用高层输出衡量模块间语义耦合

用低层输出衡量模块内部耦合（语法或调用紧密度）

d. Masked LM 或 Token 预测困惑度

对每个 token 的预测困惑度（per-token loss）也可以作为指标：

某个模块 token 在上下文中困惑度低 → 模块内部语义一致性高

跨模块困惑度 → 模块间语义依赖关系

2️⃣ 技术路线细化

源码分片：

按类、函数、文件划分片段，保证每片段长度适合 Transformer 上下文。

Transformer 前向传播：

对每个片段获取：

attention 矩阵（所有层、所有 head）

token embedding（各层隐藏状态）

预测困惑度（可选）

映射到模块/类/函数粒度：

按 token 所属的类/函数/模块聚合：

内部平均 attention → 内部耦合度

跨模块 attention → 模块间耦合度

token embedding 聚类/相似度 → 补充耦合度指标

生成语义耦合度矩阵：

每个模块对应一个向量或数值指标

汇总得到 N×N 矩阵 → 可直接用于定量分析

可视化和量化分析：

聚类热图、网络图

总耦合度指标（模块度量）

可结合传统调用图增强解释性

3️⃣ 优势
指标来源	优势	备注
Attention	直接体现 Transformer 捕捉的语义关联	可量化模块间耦合度
Token embedding	捕捉语义相似性和上下文依赖	适合跨模块语义分析
Per-token loss / perplexity	捕捉模块内部一致性	可衡量模块内耦合

✅ 这些指标都是 Transformer 直接输出，不依赖 AST、调用图等传统中间表示。

4️⃣ 小结

核心思路：直接利用 Transformer 的内部机制（attention + embedding + 预测困惑度）量化源码各模块的语义耦合度。

不依赖 AST，只依赖模型对 token 的语义捕捉能力。

最终输出：模块内凝聚度 + 模块间耦合矩阵 → 可用于定量分析。