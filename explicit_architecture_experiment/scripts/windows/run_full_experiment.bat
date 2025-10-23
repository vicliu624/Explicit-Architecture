@echo off
REM 完整实验流程脚本 (Windows版本)

setlocal enabledelayedexpansion

echo 🚀 开始显性架构完整实验流程...

REM 检查参数
if "%~1"=="" (
    echo 用法: %0 ^<source_project_dir^> [output_dir]
    echo 示例: %0 .\sample_projects .\experiment_results
    exit /b 1
)

set SOURCE_DIR=%~1
set OUTPUT_DIR=%~2
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=.\experiment_results

echo 📂 源代码目录: %SOURCE_DIR%
echo 📁 输出目录: %OUTPUT_DIR%

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 1. 数据生成
echo 📊 步骤 1: 数据生成...
call run_data_generation.bat "%SOURCE_DIR%" "%OUTPUT_DIR%\dataset"

if %ERRORLEVEL% neq 0 (
    echo ❌ 数据生成失败
    exit /b 1
)

REM 2. 模型训练
echo 🤖 步骤 2: 模型训练...
call run_training.bat "%OUTPUT_DIR%\dataset\explicit_samples.json" "%OUTPUT_DIR%\dataset\non_explicit_samples.json" "gpt2" "%OUTPUT_DIR%\models"

if %ERRORLEVEL% neq 0 (
    echo ❌ 模型训练失败
    exit /b 1
)

REM 3. 评估分析
echo 📈 步骤 3: 评估分析...
call run_evaluation.bat "%OUTPUT_DIR%\models\explicit_model" "%OUTPUT_DIR%\models\implicit_model" "%OUTPUT_DIR%\dataset\test.json" "%OUTPUT_DIR%\evaluation"

if %ERRORLEVEL% neq 0 (
    echo ❌ 评估分析失败
    exit /b 1
)

REM 4. 生成分析报告
echo 📋 步骤 4: 生成分析报告...
python ..\..\analysis\generate_report.py --explicit_eval "%OUTPUT_DIR%\evaluation\explicit_evaluation.jsonl" --implicit_eval "%OUTPUT_DIR%\evaluation\implicit_evaluation.jsonl" --coupling_report "%OUTPUT_DIR%\dataset\coupling_report.csv" --attention_analysis "%OUTPUT_DIR%\evaluation\attention_analysis" --probe_analysis "%OUTPUT_DIR%\evaluation\probe_analysis" --output "%OUTPUT_DIR%\final_report.json" --output_dir "%OUTPUT_DIR%\report_output"

if %ERRORLEVEL% neq 0 (
    echo ⚠️ 报告生成失败，但实验已完成
)

echo ✅ 完整实验流程完成!
echo 📊 最终结果:
echo    - 数据集: %OUTPUT_DIR%\dataset\
echo    - 模型: %OUTPUT_DIR%\models\
echo    - 评估: %OUTPUT_DIR%\evaluation\
echo    - 最终报告: %OUTPUT_DIR%\final_report.json
echo.
echo 🎯 实验总结:
echo    显性架构实验已完成，请查看最终报告了解详细结果。

endlocal
