# 评估分析脚本 (PowerShell版本)

param(
    [Parameter(Mandatory=$true)]
    [string]$ExplicitModel,
    
    [Parameter(Mandatory=$true)]
    [string]$ImplicitModel,
    
    [Parameter(Mandatory=$true)]
    [string]$TestData,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\evaluation_out"
)

Write-Host "🚀 开始显性架构实验评估分析..." -ForegroundColor Green

Write-Host "🤖 显性架构模型: $ExplicitModel" -ForegroundColor Cyan
Write-Host "🤖 非显性架构模型: $ImplicitModel" -ForegroundColor Cyan
Write-Host "📊 测试数据: $TestData" -ForegroundColor Cyan
Write-Host "📁 输出目录: $OutputDir" -ForegroundColor Cyan

# 检查模型目录是否存在
if (-not (Test-Path $ExplicitModel)) {
    Write-Host "❌ 错误: 显性架构模型目录不存在: $ExplicitModel" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ImplicitModel)) {
    Write-Host "❌ 错误: 非显性架构模型目录不存在: $ImplicitModel" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $TestData)) {
    Write-Host "❌ 错误: 测试数据文件不存在: $TestData" -ForegroundColor Red
    exit 1
}

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # 评估显性架构模型
    Write-Host "📊 评估显性架构模型..." -ForegroundColor Yellow
    python "..\..\evaluation\eval_pipeline.py" --model_dir $ExplicitModel --test_file $TestData --output "$OutputDir\explicit_evaluation.jsonl" --max_new_tokens 256
    
    if ($LASTEXITCODE -ne 0) {
        throw "显性架构模型评估失败"
    }
    
    # 评估非显性架构模型
    Write-Host "📊 评估非显性架构模型..." -ForegroundColor Yellow
    python "..\..\evaluation\eval_pipeline.py" --model_dir $ImplicitModel --test_file $TestData --output "$OutputDir\implicit_evaluation.jsonl" --max_new_tokens 256
    
    if ($LASTEXITCODE -ne 0) {
        throw "非显性架构模型评估失败"
    }
    
    # 提取注意力分析
    Write-Host "🔍 提取注意力分析..." -ForegroundColor Yellow
    python "..\..\evaluation\attention_extractor.py" --model_dir $ExplicitModel --test_file $TestData --output_dir "$OutputDir\attention_analysis" --max_length 512
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ 注意力分析失败，但评估已完成" -ForegroundColor Yellow
    }
    
    # 训练线性探针
    Write-Host "🧪 训练线性探针..." -ForegroundColor Yellow
    python "..\..\evaluation\probe_trainer.py" --model_dir $ExplicitModel --explicit_data $TestData --implicit_data $TestData --output_dir "$OutputDir\probe_analysis"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ 探针训练失败，但评估已完成" -ForegroundColor Yellow
    }
    
    Write-Host "✅ 评估分析完成!" -ForegroundColor Green
    Write-Host "📊 输出文件:" -ForegroundColor Cyan
    Write-Host "   - 显性架构评估: $OutputDir\explicit_evaluation.jsonl" -ForegroundColor White
    Write-Host "   - 非显性架构评估: $OutputDir\implicit_evaluation.jsonl" -ForegroundColor White
    Write-Host "   - 注意力分析: $OutputDir\attention_analysis\" -ForegroundColor White
    Write-Host "   - 探针分析: $OutputDir\probe_analysis\" -ForegroundColor White
    
} catch {
    Write-Host "❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
