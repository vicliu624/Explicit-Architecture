@echo off
REM Windows快速安装脚本

echo 🚀 开始安装显性架构实验环境...

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 错误: Python未安装或不在PATH中
    echo 请先安装Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
python --version

REM 创建虚拟环境
echo 📦 创建虚拟环境...
if exist venv (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级pip
echo 📈 升级pip...
python -m pip install --upgrade pip

REM 安装PyTorch
echo 🤖 安装PyTorch...
pip install torch torchvision torchaudio

REM 安装其他依赖
echo 📚 安装其他依赖包...
pip install -r requirements.txt

REM 验证安装
echo 🔍 验证安装...
python -c "import torch, transformers, datasets, sklearn, networkx; print('✅ 所有核心包安装成功')"

if %ERRORLEVEL% neq 0 (
    echo ❌ 安装验证失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo 🎉 安装完成！
echo.
echo 📋 下一步：
echo 1. 激活虚拟环境: venv\Scripts\activate.bat
echo 2. 准备你的Java项目数据
echo 3. 运行实验: .\scripts\windows\run_full_experiment.ps1 -SourceDir .\your_java_project
echo.
pause
