# 直接对比实验指南

## 🎯 实验目标

对比MVC架构（非显性架构）与显性架构在函数补全任务上的性能差异。

## 📁 项目结构要求

### MVC项目（非显性架构）
```
mvc_project/
├── src/
│   ├── controllers/
│   │   ├── UserController.java
│   │   └── OrderController.java
│   ├── models/
│   │   ├── User.java
│   │   └── Order.java
│   └── views/
│       ├── UserView.java
│       └── OrderView.java
```

### 显性架构项目
```
explicit_project/
├── src/
│   ├── domain/
│   │   ├── user/
│   │   │   ├── UserService.java
│   │   │   ├── UserRepository.java
│   │   │   └── User.java
│   │   └── order/
│   │       ├── OrderService.java
│   │       ├── OrderRepository.java
│   │       └── Order.java
│   └── infrastructure/
│       └── database/
│           └── DatabaseConfig.java
```

## 🚀 运行实验

### 1. 准备环境
```powershell
# 激活conda环境
conda activate explicit_architecture_experime

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行直接对比实验
```powershell
.\scripts\windows\run_direct_comparison.ps1 -MvcSourceDir ".\your_mvc_project" -ExplicitSourceDir ".\your_explicit_project"
```

### 3. 查看结果
实验完成后，结果将保存在 `direct_comparison_results/` 目录中：

```
direct_comparison_results/
├── mvc_dataset/
│   ├── samples_train.json
│   ├── samples_val.json
│   ├── samples_test.json
│   ├── coupling_report.csv
│   └── non_explicit_coupling_distribution.png
├── explicit_dataset/
│   ├── samples_train.json
│   ├── samples_val.json
│   ├── samples_test.json
│   ├── coupling_report.csv
│   └── explicit_coupling_distribution.png
├── mvc_models/
├── explicit_models/
├── mvc_evaluation/
├── explicit_evaluation/
├── report_output/
│   ├── mvc_vs_explicit_comparison.png
│   └── coupling_distribution_comparison.png
└── direct_comparison_report.json
```

## 📊 结果分析

### 1. 性能对比
- **Exact Match准确率**：显性架构 vs MVC架构
- **性能提升百分比**：显性架构相对于MVC架构的改进

### 2. 耦合度分析
- **平均耦合度**：两种架构的耦合度对比
- **分布差异**：耦合度分布的统计差异
- **显著性检验**：p值检验结果

### 3. 可视化图表
- **性能对比柱状图**：准确率对比
- **耦合度对比图**：平均耦合度对比
- **分布对比箱线图**：耦合度分布对比

## 🔧 自定义参数

### 修改输出目录
```powershell
.\scripts\windows\run_direct_comparison.ps1 -MvcSourceDir ".\mvc" -ExplicitSourceDir ".\explicit" -OutputDir ".\my_results"
```

### 单独运行数据生成
```powershell
# 处理MVC项目
python data_generation\direct_data_builder.py --src ".\mvc_project" --out ".\mvc_dataset" --view_type "non_explicit"

# 处理显性架构项目
python data_generation\direct_data_builder.py --src ".\explicit_project" --out ".\explicit_dataset" --view_type "explicit"
```

## 📋 实验报告

最终报告 `direct_comparison_report.json` 包含：

```json
{
  "experiment_type": "MVC架构 vs 显性架构直接对比",
  "summary": {
    "mvc_architecture": {
      "exact_match_accuracy": 0.750,
      "total_samples": 1000,
      "correct_samples": 750
    },
    "explicit_architecture": {
      "exact_match_accuracy": 0.820,
      "total_samples": 1000,
      "correct_samples": 820
    },
    "performance_difference": {
      "accuracy_delta": 0.070,
      "improvement_percentage": 9.3
    }
  },
  "coupling_analysis": {
    "mvc_averages": {
      "coupling_score": 5.2
    },
    "explicit_averages": {
      "coupling_score": 3.8
    }
  },
  "conclusions": {
    "performance": "显性架构在函数补全任务上表现更好",
    "coupling": "显性架构具有更低的耦合度"
  }
}
```

## 🎯 预期结果

如果显性架构假设成立，你应该看到：

1. **性能提升**：显性架构的Exact Match准确率更高
2. **耦合度降低**：显性架构的平均耦合度更低
3. **统计显著性**：差异具有统计显著性（p < 0.05）

## 🔍 故障排除

### 常见问题

1. **Python环境问题**
   ```powershell
   # 使用Anaconda Prompt
   conda activate explicit_architecture_experime
   ```

2. **依赖包缺失**
   ```powershell
   pip install -r requirements.txt
   ```

3. **路径问题**
   - 确保项目路径正确
   - 使用绝对路径避免相对路径问题

4. **权限问题**
   ```powershell
   # 设置PowerShell执行策略
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## 📞 支持

如果遇到问题，请检查：
1. Python环境是否正确激活
2. 依赖包是否完整安装
3. 项目路径是否正确
4. 文件权限是否足够
