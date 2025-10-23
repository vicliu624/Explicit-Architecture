@echo off
REM 评估分析脚本 (Windows版本)

setlocal enabledelayedexpansion

echo 🚀 开始显性架构实验评估分析...

REM 检查参数
if "%~4"=="" (
    echo 用法: %0 ^<explicit_model^> ^<implicit_model^> ^<test_data^> [output_dir]
    echo 示例: %0 .\outputs\explicit_model .\outputs\implicit_model .\dataset_out\test.json .\evaluation_out
    exit /b 1
)

set EXPLICIT_MODEL=%~1
set IMPLICIT_MODEL=%~2
set TEST_DATA=%~3
set OUTPUT_DIR=%~4
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=.\evaluation_out

echo 🤖 显性架构模型: %EXPLICIT_MODEL%
echo 🤖 非显性架构模型: %IMPLICIT_MODEL%
echo 📊 测试数据: %TEST_DATA%
echo 📁 输出目录: %OUTPUT_DIR%

REM 检查模型目录是否存在
if not exist "%EXPLICIT_MODEL%" (
    echo ❌ 错误: 显性架构模型目录不存在: %EXPLICIT_MODEL%
    exit /b 1
)

if not exist "%IMPLICIT_MODEL%" (
    echo ❌ 错误: 非显性架构模型目录不存在: %IMPLICIT_MODEL%
    exit /b 1
)

if not exist "%TEST_DATA%" (
    echo ❌ 错误: 测试数据文件不存在: %TEST_DATA%
    exit /b 1
)

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 评估显性架构模型
echo 📊 评估显性架构模型...
python ..\..\evaluation\eval_pipeline.py --model_dir "%EXPLICIT_MODEL%" --test_file "%TEST_DATA%" --output "%OUTPUT_DIR%\explicit_evaluation.jsonl" --max_new_tokens 256

if %ERRORLEVEL% neq 0 (
    echo ❌ 显性架构模型评估失败
    exit /b 1
)

REM 评估非显性架构模型
echo 📊 评估非显性架构模型...
python ..\..\evaluation\eval_pipeline.py --model_dir "%IMPLICIT_MODEL%" --test_file "%TEST_DATA%" --output "%OUTPUT_DIR%\implicit_evaluation.jsonl" --max_new_tokens 256

if %ERRORLEVEL% neq 0 (
    echo ❌ 非显性架构模型评估失败
    exit /b 1
)

REM 提取注意力分析
echo 🔍 提取注意力分析...
python ..\..\evaluation\attention_extractor.py --model_dir "%EXPLICIT_MODEL%" --test_file "%TEST_DATA%" --output_dir "%OUTPUT_DIR%\attention_analysis" --max_length 512

if %ERRORLEVEL% neq 0 (
    echo ⚠️ 注意力分析失败，但评估已完成
)

REM 训练线性探针
echo 🧪 训练线性探针...
python ..\..\evaluation\probe_trainer.py --model_dir "%EXPLICIT_MODEL%" --explicit_data "%TEST_DATA%" --implicit_data "%TEST_DATA%" --output_dir "%OUTPUT_DIR%\probe_analysis"

if %ERRORLEVEL% neq 0 (
    echo ⚠️ 探针训练失败，但评估已完成
)

echo ✅ 评估分析完成!
echo 📊 输出文件:
echo    - 显性架构评估: %OUTPUT_DIR%\explicit_evaluation.jsonl
echo    - 非显性架构评估: %OUTPUT_DIR%\implicit_evaluation.jsonl
echo    - 注意力分析: %OUTPUT_DIR%\attention_analysis\
echo    - 探针分析: %OUTPUT_DIR%\probe_analysis\

endlocal
