# 直接对比实验脚本 (PowerShell版本)
# 用于对比：MVC架构(非显性) vs 显性架构
# 直接使用两个项目，不生成副本

param(
    [Parameter(Mandatory=$true)]
    [string]$MvcSourceDir,  # MVC架构项目目录（非显性）
    
    [Parameter(Mandatory=$true)]
    [string]$ExplicitSourceDir,  # 显性架构项目目录
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\direct_comparison_results"
)

Write-Host "🚀 开始直接对比实验流程..." -ForegroundColor Green
Write-Host "📂 MVC架构目录: $MvcSourceDir" -ForegroundColor Cyan
Write-Host "📂 显性架构目录: $ExplicitSourceDir" -ForegroundColor Cyan
Write-Host "📁 输出目录: $OutputDir" -ForegroundColor Cyan

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # 1. 数据生成 - 直接处理两个项目
    Write-Host "📊 步骤 1: 数据生成..." -ForegroundColor Yellow
    
    # 处理MVC项目（作为非显性架构）
    Write-Host "🔧 处理MVC项目（非显性架构）..." -ForegroundColor Yellow
    python "..\..\data_generation\direct_data_builder.py" --src $MvcSourceDir --out "$OutputDir\mvc_dataset" --view_type "non_explicit"
    
    if ($LASTEXITCODE -ne 0) {
        throw "MVC项目数据生成失败"
    }
    
    # 处理显性架构项目
    Write-Host "🔧 处理显性架构项目..." -ForegroundColor Yellow
    python "..\..\data_generation\direct_data_builder.py" --src $ExplicitSourceDir --out "$OutputDir\explicit_dataset" --view_type "explicit"
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构项目数据生成失败"
    }
    
    # 2. 模型训练 - 分别训练两个模型
    Write-Host "🤖 步骤 2: 模型训练..." -ForegroundColor Yellow
    
    # 训练MVC模型
    Write-Host "🔧 训练MVC架构模型..." -ForegroundColor Yellow
    python "..\..\training\finetune.py" --config "..\..\training\configs\finetune_config.json" --train_file "$OutputDir\mvc_dataset\samples_train.json" --validation_file "$OutputDir\mvc_dataset\samples_val.json" --output_dir "$OutputDir\mvc_models"
    
    if ($LASTEXITCODE -ne 0) {
        throw "MVC模型训练失败"
    }
    
    # 训练显性架构模型
    Write-Host "🔧 训练显性架构模型..." -ForegroundColor Yellow
    python "..\..\training\finetune.py" --config "..\..\training\configs\finetune_config.json" --train_file "$OutputDir\explicit_dataset\samples_train.json" --validation_file "$OutputDir\explicit_dataset\samples_val.json" --output_dir "$OutputDir\explicit_models"
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构模型训练失败"
    }
    
    # 3. 评估分析 - 对比两个模型
    Write-Host "📈 步骤 3: 评估分析..." -ForegroundColor Yellow
    
    # 评估MVC模型
    Write-Host "🔧 评估MVC架构模型..." -ForegroundColor Yellow
    python "..\..\evaluation\eval_pipeline.py" --model_dir "$OutputDir\mvc_models" --test_file "$OutputDir\mvc_dataset\samples_test.json" --output "$OutputDir\mvc_evaluation\predictions.jsonl"
    
    if ($LASTEXITCODE -ne 0) {
        throw "MVC模型评估失败"
    }
    
    # 评估显性架构模型
    Write-Host "🔧 评估显性架构模型..." -ForegroundColor Yellow
    python "..\..\evaluation\eval_pipeline.py" --model_dir "$OutputDir\explicit_models" --test_file "$OutputDir\explicit_dataset\samples_test.json" --output "$OutputDir\explicit_evaluation\predictions.jsonl"
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构模型评估失败"
    }
    
    # 4. 生成对比分析报告
    Write-Host "📋 步骤 4: 生成对比分析报告..." -ForegroundColor Yellow
    python "..\..\analysis\generate_direct_comparison_report.py" --mvc_predictions "$OutputDir\mvc_evaluation\predictions.jsonl" --explicit_predictions "$OutputDir\explicit_evaluation\predictions.jsonl" --mvc_coupling "$OutputDir\mvc_dataset\coupling_report.csv" --explicit_coupling "$OutputDir\explicit_dataset\coupling_report.csv" --output "$OutputDir\direct_comparison_report.json" --output_dir "$OutputDir\report_output"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ 对比报告生成失败，但实验已完成" -ForegroundColor Yellow
    }
    
    Write-Host "✅ 直接对比实验流程完成!" -ForegroundColor Green
    Write-Host "📊 最终结果:" -ForegroundColor Cyan
    Write-Host "   - MVC数据集: $OutputDir\mvc_dataset\" -ForegroundColor White
    Write-Host "   - 显性架构数据集: $OutputDir\explicit_dataset\" -ForegroundColor White
    Write-Host "   - MVC模型: $OutputDir\mvc_models\" -ForegroundColor White
    Write-Host "   - 显性架构模型: $OutputDir\explicit_models\" -ForegroundColor White
    Write-Host "   - 对比报告: $OutputDir\direct_comparison_report.json" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 实验总结:" -ForegroundColor Green
    Write-Host "   MVC架构 vs 显性架构直接对比实验已完成，请查看对比报告了解详细结果。" -ForegroundColor White
    
} catch {
    Write-Host "❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
