# 反向对比实验脚本 (PowerShell版本)
# 用于对比：MVC架构(非显性) vs 显性架构

param(
    [Parameter(Mandatory=$true)]
    [string]$MvcSourceDir,  # MVC架构项目目录
    
    [Parameter(Mandatory=$true)]
    [string]$ExplicitSourceDir,  # 显性架构项目目录
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\reverse_experiment_results"
)

Write-Host "🚀 开始反向对比实验流程..." -ForegroundColor Green
Write-Host "📂 MVC架构目录: $MvcSourceDir" -ForegroundColor Cyan
Write-Host "📂 显性架构目录: $ExplicitSourceDir" -ForegroundColor Cyan
Write-Host "📁 输出目录: $OutputDir" -ForegroundColor Cyan

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # 1. 数据生成 - 分别处理两个项目
    Write-Host "📊 步骤 1: 数据生成..." -ForegroundColor Yellow
    
    # 处理MVC项目（作为非显性架构）
    Write-Host "🔧 处理MVC项目（非显性架构）..." -ForegroundColor Yellow
    & ".\run_data_generation.ps1" -SourceDir $MvcSourceDir -OutputDir "$OutputDir\mvc_dataset"
    
    if ($LASTEXITCODE -ne 0) {
        throw "MVC项目数据生成失败"
    }
    
    # 处理显性架构项目
    Write-Host "🔧 处理显性架构项目..." -ForegroundColor Yellow
    & ".\run_data_generation.ps1" -SourceDir $ExplicitSourceDir -OutputDir "$OutputDir\explicit_dataset"
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构项目数据生成失败"
    }
    
    # 2. 模型训练 - 分别训练两个模型
    Write-Host "🤖 步骤 2: 模型训练..." -ForegroundColor Yellow
    
    # 训练MVC模型
    Write-Host "🔧 训练MVC架构模型..." -ForegroundColor Yellow
    & ".\run_training.ps1" -ExplicitData "$OutputDir\mvc_dataset\explicit_samples.json" -ImplicitData "$OutputDir\mvc_dataset\non_explicit_samples.json" -ModelName "gpt2" -OutputDir "$OutputDir\mvc_models"
    
    if ($LASTEXITCODE -ne 0) {
        throw "MVC模型训练失败"
    }
    
    # 训练显性架构模型
    Write-Host "🔧 训练显性架构模型..." -ForegroundColor Yellow
    & ".\run_training.ps1" -ExplicitData "$OutputDir\explicit_dataset\explicit_samples.json" -ImplicitData "$OutputDir\explicit_dataset\non_explicit_samples.json" -ModelName "gpt2" -OutputDir "$OutputDir\explicit_models"
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构模型训练失败"
    }
    
    # 3. 评估分析 - 对比两个模型
    Write-Host "📈 步骤 3: 评估分析..." -ForegroundColor Yellow
    
    # 评估MVC模型
    Write-Host "🔧 评估MVC架构模型..." -ForegroundColor Yellow
    & ".\run_evaluation.ps1" -ExplicitModel "$OutputDir\mvc_models\explicit_model" -ImplicitModel "$OutputDir\mvc_models\implicit_model" -TestData "$OutputDir\mvc_dataset\test.json" -OutputDir "$OutputDir\mvc_evaluation"
    
    if ($LASTEXITCODE -ne 0) {
        throw "MVC模型评估失败"
    }
    
    # 评估显性架构模型
    Write-Host "🔧 评估显性架构模型..." -ForegroundColor Yellow
    & ".\run_evaluation.ps1" -ExplicitModel "$OutputDir\explicit_models\explicit_model" -ImplicitModel "$OutputDir\explicit_models\implicit_model" -TestData "$OutputDir\explicit_dataset\test.json" -OutputDir "$OutputDir\explicit_evaluation"
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构模型评估失败"
    }
    
    # 4. 生成对比分析报告
    Write-Host "📋 步骤 4: 生成对比分析报告..." -ForegroundColor Yellow
    python "..\..\analysis\generate_reverse_report.py" --mvc_eval "$OutputDir\mvc_evaluation" --explicit_eval "$OutputDir\explicit_evaluation" --mvc_coupling "$OutputDir\mvc_dataset\coupling_report.csv" --explicit_coupling "$OutputDir\explicit_dataset\coupling_report.csv" --output "$OutputDir\reverse_comparison_report.json" --output_dir "$OutputDir\report_output"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ 对比报告生成失败，但实验已完成" -ForegroundColor Yellow
    }
    
    Write-Host "✅ 反向对比实验流程完成!" -ForegroundColor Green
    Write-Host "📊 最终结果:" -ForegroundColor Cyan
    Write-Host "   - MVC数据集: $OutputDir\mvc_dataset\" -ForegroundColor White
    Write-Host "   - 显性架构数据集: $OutputDir\explicit_dataset\" -ForegroundColor White
    Write-Host "   - MVC模型: $OutputDir\mvc_models\" -ForegroundColor White
    Write-Host "   - 显性架构模型: $OutputDir\explicit_models\" -ForegroundColor White
    Write-Host "   - 对比报告: $OutputDir\reverse_comparison_report.json" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 实验总结:" -ForegroundColor Green
    Write-Host "   MVC架构 vs 显性架构对比实验已完成，请查看对比报告了解详细结果。" -ForegroundColor White
    
} catch {
    Write-Host "❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
