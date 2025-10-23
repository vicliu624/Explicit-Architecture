#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境测试脚本
用于验证Python环境和依赖包是否正确安装
"""

import sys
import importlib
from typing import List, Tuple

def check_python_version() -> bool:
    """检查Python版本"""
    version = sys.version_info
    print(f"🐍 Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print("✅ Python版本符合要求")
    return True

def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """检查单个包是否安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', '未知版本')
        print(f"✅ {package_name}: {version}")
        return True, version
    except ImportError:
        print(f"❌ {package_name}: 未安装")
        return False, "未安装"

def check_core_packages() -> bool:
    """检查核心包"""
    print("\n📦 检查核心包...")
    
    core_packages = [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("datasets", "datasets"),
        ("scikit-learn", "sklearn"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("scipy", "scipy"),
    ]
    
    all_installed = True
    for package_name, import_name in core_packages:
        installed, version = check_package(package_name, import_name)
        if not installed:
            all_installed = False
    
    return all_installed

def check_optional_packages() -> bool:
    """检查可选包"""
    print("\n🔧 检查可选包...")
    
    optional_packages = [
        ("tree-sitter", "tree_sitter"),
        ("tree-sitter-languages", "tree_sitter_languages"),
        ("networkx", "networkx"),
        ("tqdm", "tqdm"),
        ("evaluate", "evaluate"),
        ("jupyter", "jupyter"),
    ]
    
    installed_count = 0
    for package_name, import_name in optional_packages:
        installed, version = check_package(package_name, import_name)
        if installed:
            installed_count += 1
    
    print(f"📊 可选包安装情况: {installed_count}/{len(optional_packages)}")
    return installed_count >= len(optional_packages) // 2

def check_pytorch_cuda() -> bool:
    """检查PyTorch CUDA支持"""
    print("\n🚀 检查PyTorch CUDA支持...")
    
    try:
        import torch
        print(f"PyTorch版本: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA可用: {torch.cuda.get_device_name(0)}")
            print(f"CUDA版本: {torch.version.cuda}")
            return True
        else:
            print("⚠️ CUDA不可用，将使用CPU")
            return False
    except ImportError:
        print("❌ PyTorch未安装")
        return False

def check_data_generation() -> bool:
    """检查数据生成功能"""
    print("\n🔍 检查数据生成功能...")
    
    try:
        # 测试多语言文件检测
        import os
        from pathlib import Path
        
        # 创建临时测试文件
        test_files = [
            "test.py",
            "test.java", 
            "test.js",
            "test.ts",
            "test.cpp",
            "test.cs"
        ]
        
        temp_dir = Path("temp_test")
        temp_dir.mkdir(exist_ok=True)
        
        for file in test_files:
            (temp_dir / file).touch()
        
        # 测试文件检测
        supported_extensions = ['.py', '.java', '.js', '.ts', '.cpp', '.c', '.cs', '.go', '.rs']
        found_files = []
        
        for file_path in temp_dir.iterdir():
            if file_path.suffix in supported_extensions:
                found_files.append(file_path.name)
        
        # 清理测试文件
        import shutil
        shutil.rmtree(temp_dir)
        
        print(f"✅ 支持的文件类型: {supported_extensions}")
        print(f"✅ 检测到测试文件: {found_files}")
        return True
        
    except Exception as e:
        print(f"❌ 数据生成功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 显性架构实验环境测试")
    print("=" * 50)
    
    # 检查Python版本
    python_ok = check_python_version()
    
    # 检查核心包
    core_ok = check_core_packages()
    
    # 检查可选包
    optional_ok = check_optional_packages()
    
    # 检查PyTorch CUDA
    cuda_ok = check_pytorch_cuda()
    
    # 检查数据生成功能
    data_gen_ok = check_data_generation()
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"Python版本: {'✅' if python_ok else '❌'}")
    print(f"核心包: {'✅' if core_ok else '❌'}")
    print(f"可选包: {'✅' if optional_ok else '⚠️'}")
    print(f"CUDA支持: {'✅' if cuda_ok else '⚠️'}")
    print(f"数据生成: {'✅' if data_gen_ok else '❌'}")
    
    if python_ok and core_ok and data_gen_ok:
        print("\n🎉 环境测试通过！可以开始实验了。")
        print("\n📋 下一步:")
        print("1. 准备你的Java项目数据")
        print("2. 运行实验脚本")
        print("3. 查看实验结果")
        return True
    else:
        print("\n❌ 环境测试失败，请检查安装。")
        print("\n🔧 解决方案:")
        if not python_ok:
            print("- 升级Python到3.8+版本")
        if not core_ok:
            print("- 运行: pip install -r requirements.txt")
        if not data_gen_ok:
            print("- 检查文件权限和路径")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
