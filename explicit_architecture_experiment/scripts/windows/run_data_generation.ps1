# 数据生成脚本 (PowerShell版本)

param(
    [Parameter(Mandatory=$true)]
    [string]$SourceDir,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\dataset_out"
)

Write-Host "🚀 开始显性架构实验数据生成..." -ForegroundColor Green

Write-Host "📂 源代码目录: $SourceDir" -ForegroundColor Cyan
Write-Host "📁 输出目录: $OutputDir" -ForegroundColor Cyan

# 检查源代码目录是否存在
if (-not (Test-Path $SourceDir)) {
    Write-Host "❌ 错误: 源代码目录不存在: $SourceDir" -ForegroundColor Red
    exit 1
}

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # 运行数据生成脚本
    Write-Host "🔧 运行数据生成脚本..." -ForegroundColor Yellow
    python "..\..\data_generation\data_builder.py" --src $SourceDir --out $OutputDir
    
    if ($LASTEXITCODE -ne 0) {
        throw "数据生成脚本执行失败"
    }
    
    # 运行耦合度分析
    Write-Host "🔍 运行耦合度分析..." -ForegroundColor Yellow
    python "..\..\data_generation\coupling_analyzer.py" --explicit_dir "$OutputDir\explicit_view" --implicit_dir "$OutputDir\non_explicit_view" --output_dir "$OutputDir\coupling_analysis"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ 耦合度分析失败，但数据生成已完成" -ForegroundColor Yellow
    }
    
    Write-Host "✅ 数据生成完成!" -ForegroundColor Green
    Write-Host "📊 输出文件:" -ForegroundColor Cyan
    Write-Host "   - 显性架构样本: $OutputDir\explicit_samples.json" -ForegroundColor White
    Write-Host "   - 非显性架构样本: $OutputDir\non_explicit_samples.json" -ForegroundColor White
    Write-Host "   - 耦合度报告: $OutputDir\coupling_report.csv" -ForegroundColor White
    Write-Host "   - 耦合度对比图: $OutputDir\coupling_comparison.png" -ForegroundColor White
    
} catch {
    Write-Host "❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
