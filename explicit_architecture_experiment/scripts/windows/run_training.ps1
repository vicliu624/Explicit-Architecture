# 模型训练脚本 (PowerShell版本)

param(
    [Parameter(Mandatory=$true)]
    [string]$ExplicitData,
    
    [Parameter(Mandatory=$true)]
    [string]$ImplicitData,
    
    [Parameter(Mandatory=$false)]
    [string]$ModelName = "gpt2",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\outputs"
)

Write-Host "🚀 开始显性架构实验模型训练..." -ForegroundColor Green

Write-Host "📊 显性架构数据: $ExplicitData" -ForegroundColor Cyan
Write-Host "📊 非显性架构数据: $ImplicitData" -ForegroundColor Cyan
Write-Host "🤖 模型名称: $ModelName" -ForegroundColor Cyan
Write-Host "📁 输出目录: $OutputDir" -ForegroundColor Cyan

# 检查数据文件是否存在
if (-not (Test-Path $ExplicitData)) {
    Write-Host "❌ 错误: 显性架构数据文件不存在: $ExplicitData" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ImplicitData)) {
    Write-Host "❌ 错误: 非显性架构数据文件不存在: $ImplicitData" -ForegroundColor Red
    exit 1
}

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # 训练显性架构模型
    Write-Host "🔧 训练显性架构模型..." -ForegroundColor Yellow
    python "..\..\training\finetune.py" --model_name $ModelName --output_dir "$OutputDir\explicit_model" --train_file $ExplicitData --val_file $ExplicitData --epochs 3 --batch_size 4 --learning_rate 5e-5
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构模型训练失败"
    }
    
    # 训练非显性架构模型
    Write-Host "🔧 训练非显性架构模型..." -ForegroundColor Yellow
    python "..\..\training\finetune.py" --model_name $ModelName --output_dir "$OutputDir\implicit_model" --train_file $ImplicitData --val_file $ImplicitData --epochs 3 --batch_size 4 --learning_rate 5e-5
    
    if ($LASTEXITCODE -ne 0) {
        throw "非显性架构模型训练失败"
    }
    
    Write-Host "✅ 模型训练完成!" -ForegroundColor Green
    Write-Host "📊 输出模型:" -ForegroundColor Cyan
    Write-Host "   - 显性架构模型: $OutputDir\explicit_model" -ForegroundColor White
    Write-Host "   - 非显性架构模型: $OutputDir\implicit_model" -ForegroundColor White
    
} catch {
    Write-Host "❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
