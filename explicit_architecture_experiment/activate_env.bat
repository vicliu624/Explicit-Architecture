@echo off
REM 激活conda环境的批处理脚本

echo 🚀 激活显性架构实验环境
echo ========================

REM 设置环境变量
set CONDA_DEFAULT_ENV=explicit_architecture_experime
set CONDA_PREFIX=C:\Users\vicliu\.conda\envs\explicit_architecture_experime
set PATH=%CONDA_PREFIX%;%CONDA_PREFIX%\Scripts;%CONDA_PREFIX%\Library\bin;%PATH%

echo ✅ 环境变量已设置
echo 📍 Python路径: %CONDA_PREFIX%\python.exe
echo.

REM 验证Python
%CONDA_PREFIX%\python.exe --version
if %ERRORLEVEL% neq 0 (
    echo ❌ Python不可用
    pause
    exit /b 1
)

echo ✅ Python可用
echo.
echo 🎯 现在你可以运行：
echo   python test_environment.py
echo   pip install -r requirements.txt
echo   python data_generation/data_builder.py --help
echo.

REM 保持环境激活状态
cmd /k