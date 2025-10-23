@echo off
REM 数据生成脚本 (Windows版本)

setlocal enabledelayedexpansion

echo 🚀 开始显性架构实验数据生成...

REM 检查参数
if "%~1"=="" (
    echo 用法: %0 ^<source_project_dir^> [output_dir]
    echo 示例: %0 .\sample_projects .\dataset_out
    exit /b 1
)

set SOURCE_DIR=%~1
set OUTPUT_DIR=%~2
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=.\dataset_out

echo 📂 源代码目录: %SOURCE_DIR%
echo 📁 输出目录: %OUTPUT_DIR%

REM 检查源代码目录是否存在
if not exist "%SOURCE_DIR%" (
    echo ❌ 错误: 源代码目录不存在: %SOURCE_DIR%
    exit /b 1
)

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 运行数据生成脚本
echo 🔧 运行数据生成脚本...
python ..\..\data_generation\data_builder.py --src "%SOURCE_DIR%" --out "%OUTPUT_DIR%"

if %ERRORLEVEL% neq 0 (
    echo ❌ 数据生成失败
    exit /b 1
)

REM 运行耦合度分析
echo 🔍 运行耦合度分析...
python ..\..\data_generation\coupling_analyzer.py --explicit_dir "%OUTPUT_DIR%\explicit_view" --implicit_dir "%OUTPUT_DIR%\non_explicit_view" --output_dir "%OUTPUT_DIR%\coupling_analysis"

if %ERRORLEVEL% neq 0 (
    echo ⚠️ 耦合度分析失败，但数据生成已完成
)

echo ✅ 数据生成完成!
echo 📊 输出文件:
echo    - 显性架构样本: %OUTPUT_DIR%\explicit_samples.json
echo    - 非显性架构样本: %OUTPUT_DIR%\non_explicit_samples.json
echo    - 耦合度报告: %OUTPUT_DIR%\coupling_report.csv
echo    - 耦合度对比图: %OUTPUT_DIR%\coupling_comparison.png

endlocal
