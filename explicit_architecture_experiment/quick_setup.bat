@echo off
REM 快速设置脚本

echo 🚀 显性架构实验快速设置
echo ================================

REM 尝试激活conda环境
echo 🔍 尝试激活conda环境...
call C:\Users\vicliu\.conda\envs\explicit_architecture_experime\Scripts\activate.bat
if %ERRORLEVEL% equ 0 (
    echo ✅ Conda环境激活成功！
    goto :check_python
)

echo ❌ Conda环境激活失败，使用系统Python...

:check_python
echo.
echo 🐍 检查Python环境...
python --version
if %ERRORLEVEL% neq 0 (
    echo ❌ Python不可用
    pause
    exit /b 1
)

echo.
echo 📦 检查关键包...
python -c "import sys; print(f'Python版本: {sys.version}')" 2>nul
python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>nul || echo "PyTorch: 未安装"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')" 2>nul || echo "Transformers: 未安装"

echo.
echo 📋 下一步操作：
echo 1. 安装依赖: pip install -r requirements.txt
echo 2. 测试环境: python test_environment.py
echo 3. 开始实验: .\scripts\windows\run_full_experiment.ps1 -SourceDir .\your_java_project

echo.
echo 按任意键继续...
pause >nul

