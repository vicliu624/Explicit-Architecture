@echo off
echo 🚀 简单环境测试
echo ================

echo 📍 当前目录: %CD%
echo.

echo 🐍 测试Python环境...
echo 方法1: 使用conda环境路径
C:\Users\vicliu\.conda\envs\explicit_architecture_experime\python.exe --version
if %ERRORLEVEL% equ 0 (
    echo ✅ 找到conda环境中的Python
    goto :test_packages
)

echo 方法2: 使用系统Python
python --version
if %ERRORLEVEL% neq 0 (
    echo ❌ Python不可用
    goto :end
)

:test_packages
echo.
echo 📦 测试关键包...
C:\Users\vicliu\.conda\envs\explicit_architecture_experime\python.exe -c "import sys; print('Python路径:', sys.executable)" 2>nul
C:\Users\vicliu\.conda\envs\explicit_architecture_experime\python.exe -c "import torch; print('PyTorch版本:', torch.__version__)" 2>nul || echo "PyTorch: 未安装"
C:\Users\vicliu\.conda\envs\explicit_architecture_experime\python.exe -c "import transformers; print('Transformers版本:', transformers.__version__)" 2>nul || echo "Transformers: 未安装"

echo.
echo 🎯 下一步：
echo 1. 如果上面显示"未安装"，运行: pip install -r requirements.txt
echo 2. 测试完整环境: python test_environment.py

:end
echo.
echo 按任意键退出...
pause >nul

