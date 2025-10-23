# 完整实验流程脚本 (PowerShell版本)

param(
    [Parameter(Mandatory=$true)]
    [string]$SourceDir,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\experiment_results"
)

Write-Host "🚀 开始显性架构完整实验流程..." -ForegroundColor Green

Write-Host "📂 源代码目录: $SourceDir" -ForegroundColor Cyan
Write-Host "📁 输出目录: $OutputDir" -ForegroundColor Cyan

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # 1. 数据生成
    Write-Host "📊 步骤 1: 数据生成..." -ForegroundColor Yellow
    & ".\run_data_generation.ps1" -SourceDir $SourceDir -OutputDir "$OutputDir\dataset"
    
    if ($LASTEXITCODE -ne 0) {
        throw "数据生成失败"
    }
    
    # 2. 模型训练
    Write-Host "🤖 步骤 2: 模型训练..." -ForegroundColor Yellow
    & ".\run_training.ps1" -ExplicitData "$OutputDir\dataset\explicit_samples.json" -ImplicitData "$OutputDir\dataset\non_explicit_samples.json" -ModelName "gpt2" -OutputDir "$OutputDir\models"
    
    if ($LASTEXITCODE -ne 0) {
        throw "模型训练失败"
    }
    
    # 3. 评估分析
    Write-Host "📈 步骤 3: 评估分析..." -ForegroundColor Yellow
    & ".\run_evaluation.ps1" -ExplicitModel "$OutputDir\models\explicit_model" -ImplicitModel "$OutputDir\models\implicit_model" -TestData "$OutputDir\dataset\test.json" -OutputDir "$OutputDir\evaluation"
    
    if ($LASTEXITCODE -ne 0) {
        throw "评估分析失败"
    }
    
    # 4. 生成分析报告
    Write-Host "📋 步骤 4: 生成分析报告..." -ForegroundColor Yellow
    python "..\..\analysis\generate_report.py" --explicit_eval "$OutputDir\evaluation\explicit_evaluation.jsonl" --implicit_eval "$OutputDir\evaluation\implicit_evaluation.jsonl" --coupling_report "$OutputDir\dataset\coupling_report.csv" --attention_analysis "$OutputDir\evaluation\attention_analysis" --probe_analysis "$OutputDir\evaluation\probe_analysis" --output "$OutputDir\final_report.json" --output_dir "$OutputDir\report_output"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ 报告生成失败，但实验已完成" -ForegroundColor Yellow
    }
    
    Write-Host "✅ 完整实验流程完成!" -ForegroundColor Green
    Write-Host "📊 最终结果:" -ForegroundColor Cyan
    Write-Host "   - 数据集: $OutputDir\dataset\" -ForegroundColor White
    Write-Host "   - 模型: $OutputDir\models\" -ForegroundColor White
    Write-Host "   - 评估: $OutputDir\evaluation\" -ForegroundColor White
    Write-Host "   - 最终报告: $OutputDir\final_report.json" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 实验总结:" -ForegroundColor Green
    Write-Host "   显性架构实验已完成，请查看最终报告了解详细结果。" -ForegroundColor White
    
} catch {
    Write-Host "❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
