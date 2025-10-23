# 检查实验进度脚本
param(
    [Parameter(Mandatory=$true)]
    [string]$OutputDir
)

Write-Host "🔍 检查实验进度..." -ForegroundColor Green
Write-Host "📁 输出目录: $OutputDir" -ForegroundColor Cyan

# 检查数据生成
Write-Host "`n📊 数据生成状态:" -ForegroundColor Yellow
$MvcDataset = "$OutputDir\mvc_dataset"
$ExplicitDataset = "$OutputDir\explicit_dataset"
$MvcCoupling = "$MvcDataset\coupling_report.csv"
$ExplicitCoupling = "$ExplicitDataset\coupling_report.csv"

if ((Test-Path $MvcDataset) -and (Test-Path $MvcCoupling)) {
    Write-Host "✅ MVC项目数据: 已完成" -ForegroundColor Green
} else {
    Write-Host "❌ MVC项目数据: 未完成" -ForegroundColor Red
}

if ((Test-Path $ExplicitDataset) -and (Test-Path $ExplicitCoupling)) {
    Write-Host "✅ 显性架构项目数据: 已完成" -ForegroundColor Green
} else {
    Write-Host "❌ 显性架构项目数据: 未完成" -ForegroundColor Red
}

# 检查模型训练
Write-Host "`n🤖 模型训练状态:" -ForegroundColor Yellow
$MvcModel = "$OutputDir\mvc_models"
$ExplicitModel = "$OutputDir\explicit_models"

if (Test-Path $MvcModel) {
    Write-Host "✅ MVC模型: 已完成" -ForegroundColor Green
} else {
    Write-Host "❌ MVC模型: 未完成" -ForegroundColor Red
}

if (Test-Path $ExplicitModel) {
    Write-Host "✅ 显性架构模型: 已完成" -ForegroundColor Green
} else {
    Write-Host "❌ 显性架构模型: 未完成" -ForegroundColor Red
}

# 检查评估
Write-Host "`n📈 模型评估状态:" -ForegroundColor Yellow
$MvcEval = "$OutputDir\mvc_evaluation\predictions.jsonl"
$ExplicitEval = "$OutputDir\explicit_evaluation\predictions.jsonl"

if (Test-Path $MvcEval) {
    Write-Host "✅ MVC模型评估: 已完成" -ForegroundColor Green
} else {
    Write-Host "❌ MVC模型评估: 未完成" -ForegroundColor Red
}

if (Test-Path $ExplicitEval) {
    Write-Host "✅ 显性架构模型评估: 已完成" -ForegroundColor Green
} else {
    Write-Host "❌ 显性架构模型评估: 未完成" -ForegroundColor Red
}

# 检查最终报告
Write-Host "`n📋 分析报告状态:" -ForegroundColor Yellow
$FinalReport = "$OutputDir\direct_comparison_report.json"

if (Test-Path $FinalReport) {
    Write-Host "✅ 对比分析报告: 已完成" -ForegroundColor Green
} else {
    Write-Host "❌ 对比分析报告: 未完成" -ForegroundColor Red
}

# 总结
Write-Host "`n🎯 实验完成度:" -ForegroundColor Cyan
$CompletedSteps = 0
$TotalSteps = 5

if ((Test-Path $MvcDataset) -and (Test-Path $MvcCoupling)) { $CompletedSteps++ }
if ((Test-Path $ExplicitDataset) -and (Test-Path $ExplicitCoupling)) { $CompletedSteps++ }
if (Test-Path $MvcModel) { $CompletedSteps++ }
if (Test-Path $ExplicitModel) { $CompletedSteps++ }
if (Test-Path $FinalReport) { $CompletedSteps++ }

$Progress = [math]::Round(($CompletedSteps / $TotalSteps) * 100, 1)
Write-Host "   完成度: $Progress% ($CompletedSteps/$TotalSteps)" -ForegroundColor White

if ($Progress -eq 100) {
    Write-Host "🎉 实验已完全完成！" -ForegroundColor Green
} elseif ($Progress -ge 80) {
    Write-Host "🚀 实验接近完成！" -ForegroundColor Yellow
} else {
    Write-Host "⏳ 实验进行中..." -ForegroundColor Yellow
}
