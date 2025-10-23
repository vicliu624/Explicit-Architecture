# 直接对比实验脚本 (PowerShell版本) - 修复版
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

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
Write-Host "📁 项目根目录: $ProjectRoot" -ForegroundColor Cyan

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

try {
    # 1. 数据生成 - 直接处理两个项目
    Write-Host "📊 步骤 1: 数据生成..." -ForegroundColor Yellow
    
    # 处理MVC项目（作为非显性架构）
    $MvcDatasetDir = "$OutputDir\mvc_dataset"
    $MvcCouplingReport = "$MvcDatasetDir\coupling_report.csv"
    if ((Test-Path $MvcDatasetDir) -and (Test-Path $MvcCouplingReport)) {
        Write-Host "✅ MVC项目数据已存在，跳过数据生成: $MvcDatasetDir" -ForegroundColor Green
    } else {
        Write-Host "🔧 处理MVC项目（非显性架构）..." -ForegroundColor Yellow
        $MvcDataBuilder = Join-Path $ProjectRoot "data_generation\direct_data_builder.py"
        Write-Host "🔍 使用脚本: $MvcDataBuilder" -ForegroundColor Gray
        python $MvcDataBuilder --src $MvcSourceDir --out $MvcDatasetDir --view_type "non_explicit"
        
        if ($LASTEXITCODE -ne 0) {
            throw "MVC项目数据生成失败"
        }
    }
    
    # 处理显性架构项目
    $ExplicitDatasetDir = "$OutputDir\explicit_dataset"
    $ExplicitCouplingReport = "$ExplicitDatasetDir\coupling_report.csv"
    if ((Test-Path $ExplicitDatasetDir) -and (Test-Path $ExplicitCouplingReport)) {
        Write-Host "✅ 显性架构项目数据已存在，跳过数据生成: $ExplicitDatasetDir" -ForegroundColor Green
    } else {
        Write-Host "🔧 处理显性架构项目..." -ForegroundColor Yellow
        $ExplicitDataBuilder = Join-Path $ProjectRoot "data_generation\direct_data_builder.py"
        Write-Host "🔍 使用脚本: $ExplicitDataBuilder" -ForegroundColor Gray
        python $ExplicitDataBuilder --src $ExplicitSourceDir --out $ExplicitDatasetDir --view_type "explicit"
        
        if ($LASTEXITCODE -ne 0) {
            throw "显性架构项目数据生成失败"
        }
    }
    
    # 2. 模型训练 - 分别训练两个模型
    Write-Host "🤖 步骤 2: 模型训练..." -ForegroundColor Yellow
    
    # 训练MVC模型
    $MvcModelDir = "$OutputDir\mvc_models"
    if (Test-Path $MvcModelDir) {
        Write-Host "✅ MVC模型已存在，跳过训练: $MvcModelDir" -ForegroundColor Green
    } else {
        Write-Host "🔧 训练MVC架构模型..." -ForegroundColor Yellow
        $MvcTrainScript = Join-Path $ProjectRoot "training\finetune.py"
        $MvcConfig = Join-Path $ProjectRoot "training\configs\finetune_config.json"
        python $MvcTrainScript --config $MvcConfig --train_file "$OutputDir\mvc_dataset\samples_train.json" --val_file "$OutputDir\mvc_dataset\samples_val.json" --output_dir $MvcModelDir
        
        if ($LASTEXITCODE -ne 0) {
            throw "MVC模型训练失败"
        }
    }
    
    # 训练显性架构模型
    $ExplicitModelDir = "$OutputDir\explicit_models"
    if (Test-Path $ExplicitModelDir) {
        Write-Host "✅ 显性架构模型已存在，跳过训练: $ExplicitModelDir" -ForegroundColor Green
    } else {
        Write-Host "🔧 训练显性架构模型..." -ForegroundColor Yellow
        $ExplicitTrainScript = Join-Path $ProjectRoot "training\finetune.py"
        $ExplicitConfig = Join-Path $ProjectRoot "training\configs\finetune_config.json"
        python $ExplicitTrainScript --config $ExplicitConfig --train_file "$OutputDir\explicit_dataset\samples_train.json" --val_file "$OutputDir\explicit_dataset\samples_val.json" --output_dir $ExplicitModelDir
        
        if ($LASTEXITCODE -ne 0) {
            throw "显性架构模型训练失败"
        }
    }
    
    # 3. 评估分析 - 对比两个模型
    Write-Host "📈 步骤 3: 评估分析..." -ForegroundColor Yellow
    
    # 评估MVC模型
    $MvcEvalOutput = "$OutputDir\mvc_evaluation\predictions.jsonl"
    if (Test-Path $MvcEvalOutput) {
        Write-Host "✅ MVC模型评估结果已存在，跳过评估: $MvcEvalOutput" -ForegroundColor Green
    } else {
        Write-Host "🔧 评估MVC架构模型..." -ForegroundColor Yellow
        $MvcEvalScript = Join-Path $ProjectRoot "evaluation\eval_pipeline.py"
        python $MvcEvalScript --model_dir "$OutputDir\mvc_models" --test_file "$OutputDir\mvc_dataset\samples_test.json" --output $MvcEvalOutput
        
        if ($LASTEXITCODE -ne 0) {
            throw "MVC模型评估失败"
        }
    }
    
    # 评估显性架构模型
    $ExplicitEvalOutput = "$OutputDir\explicit_evaluation\predictions.jsonl"
    if (Test-Path $ExplicitEvalOutput) {
        Write-Host "✅ 显性架构模型评估结果已存在，跳过评估: $ExplicitEvalOutput" -ForegroundColor Green
    } else {
        Write-Host "🔧 评估显性架构模型..." -ForegroundColor Yellow
        $ExplicitEvalScript = Join-Path $ProjectRoot "evaluation\eval_pipeline.py"
        python $ExplicitEvalScript --model_dir "$OutputDir\explicit_models" --test_file "$OutputDir\explicit_dataset\samples_test.json" --output $ExplicitEvalOutput
        
        if ($LASTEXITCODE -ne 0) {
            throw "显性架构模型评估失败"
        }
    }
    
    # 4. 生成对比分析报告
    Write-Host "📋 步骤 4: 生成对比分析报告..." -ForegroundColor Yellow
    $FinalReport = "$OutputDir\direct_comparison_report.json"
    if (Test-Path $FinalReport) {
        Write-Host "✅ 对比分析报告已存在，跳过报告生成: $FinalReport" -ForegroundColor Green
    } else {
        $ReportScript = Join-Path $ProjectRoot "analysis\generate_direct_comparison_report.py"
        python $ReportScript --mvc_predictions "$OutputDir\mvc_evaluation\predictions.jsonl" --explicit_predictions "$OutputDir\explicit_evaluation\predictions.jsonl" --mvc_coupling "$OutputDir\mvc_dataset\coupling_report.csv" --explicit_coupling "$OutputDir\explicit_dataset\coupling_report.csv" --output $FinalReport --output_dir "$OutputDir\report_output"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️ 对比报告生成失败，但实验已完成" -ForegroundColor Yellow
        }
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
