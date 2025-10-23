@echo off
REM 模型训练脚本 (Windows版本)

setlocal enabledelayedexpansion

echo 🚀 开始显性架构实验模型训练...

REM 检查参数
if "%~3"=="" (
    echo 用法: %0 ^<explicit_data^> ^<implicit_data^> [model_name] [output_dir]
    echo 示例: %0 .\dataset_out\explicit_samples.json .\dataset_out\non_explicit_samples.json gpt2 .\outputs
    exit /b 1
)

set EXPLICIT_DATA=%~1
set IMPLICIT_DATA=%~2
set MODEL_NAME=%~3
if "%MODEL_NAME%"=="" set MODEL_NAME=gpt2
set OUTPUT_DIR=%~4
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=.\outputs

echo 📊 显性架构数据: %EXPLICIT_DATA%
echo 📊 非显性架构数据: %IMPLICIT_DATA%
echo 🤖 模型名称: %MODEL_NAME%
echo 📁 输出目录: %OUTPUT_DIR%

REM 检查数据文件是否存在
if not exist "%EXPLICIT_DATA%" (
    echo ❌ 错误: 显性架构数据文件不存在: %EXPLICIT_DATA%
    exit /b 1
)

if not exist "%IMPLICIT_DATA%" (
    echo ❌ 错误: 非显性架构数据文件不存在: %IMPLICIT_DATA%
    exit /b 1
)

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 训练显性架构模型
echo 🔧 训练显性架构模型...
python ..\..\training\finetune.py --model_name "%MODEL_NAME%" --output_dir "%OUTPUT_DIR%\explicit_model" --train_file "%EXPLICIT_DATA%" --val_file "%EXPLICIT_DATA%" --epochs 3 --batch_size 4 --learning_rate 5e-5

if %ERRORLEVEL% neq 0 (
    echo ❌ 显性架构模型训练失败
    exit /b 1
)

REM 训练非显性架构模型
echo 🔧 训练非显性架构模型...
python ..\..\training\finetune.py --model_name "%MODEL_NAME%" --output_dir "%OUTPUT_DIR%\implicit_model" --train_file "%IMPLICIT_DATA%" --val_file "%IMPLICIT_DATA%" --epochs 3 --batch_size 4 --learning_rate 5e-5

if %ERRORLEVEL% neq 0 (
    echo ❌ 非显性架构模型训练失败
    exit /b 1
)

echo ✅ 模型训练完成!
echo 📊 输出模型:
echo    - 显性架构模型: %OUTPUT_DIR%\explicit_model
echo    - 非显性架构模型: %OUTPUT_DIR%\implicit_model

endlocal
