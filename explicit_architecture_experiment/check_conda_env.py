#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conda环境检查脚本
"""

import os
import sys
import subprocess

def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_conda():
    """检查conda是否可用"""
    print("🔍 检查conda环境...")
    
    # 检查conda命令
    success, stdout, stderr = run_command("conda --version")
    if success:
        print(f"✅ Conda已安装: {stdout.strip()}")
        return True
    else:
        print("❌ Conda未安装或不在PATH中")
        return False

def list_conda_envs():
    """列出所有conda环境"""
    print("\n📋 所有conda环境:")
    success, stdout, stderr = run_command("conda env list")
    if success:
        print(stdout)
        return stdout
    else:
        print(f"❌ 无法获取环境列表: {stderr}")
        return ""

def check_current_env():
    """检查当前环境"""
    print("\n🔧 当前环境信息:")
    
    # 检查当前环境名称
    env_name = os.environ.get('CONDA_DEFAULT_ENV', 'None')
    print(f"当前环境: {env_name}")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    # 检查是否在conda环境中
    conda_prefix = os.environ.get('CONDA_PREFIX', '')
    if conda_prefix:
        print(f"✅ 在conda环境中: {conda_prefix}")
    else:
        print("⚠️ 不在conda环境中")

def check_packages():
    """检查关键包"""
    print("\n📦 检查关键包:")
    
    packages = [
        'torch', 'transformers', 'datasets', 'sklearn', 
        'numpy', 'pandas', 'matplotlib', 'networkx'
    ]
    
    for package in packages:
        try:
            if package == 'sklearn':
                import sklearn
                print(f"✅ {package}: {sklearn.__version__}")
            else:
                module = __import__(package)
                version = getattr(module, '__version__', '未知版本')
                print(f"✅ {package}: {version}")
        except ImportError:
            print(f"❌ {package}: 未安装")

def main():
    """主函数"""
    print("🧪 Conda环境检查工具")
    print("=" * 50)
    
    # 检查conda
    if not check_conda():
        print("\n💡 建议:")
        print("1. 安装Miniconda: https://docs.conda.io/en/latest/miniconda.html")
        print("2. 或者使用系统Python和venv")
        return
    
    # 列出环境
    list_conda_envs()
    
    # 检查当前环境
    check_current_env()
    
    # 检查包
    check_packages()
    
    print("\n" + "=" * 50)
    print("💡 使用建议:")
    print("1. 激活环境: conda activate your_env_name")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 运行测试: python test_environment.py")

if __name__ == "__main__":
    main()

