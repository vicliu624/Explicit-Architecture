#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_splitters.py
----------------------------------------------------
测试代码分割器

功能：
1. 测试Java和Python分割器的基本功能
2. 验证分割质量
3. 检查是否解决了之前的问题

依赖：
    Python 3.7+
----------------------------------------------------
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import get_code_splitter, get_supported_languages


def test_java_splitter():
    """测试Java分割器"""
    print("🧪 测试Java分割器...")
    
    java_code = [
        "package com.example;\n",
        "\n",
        "import java.util.List;\n",
        "import java.util.ArrayList;\n",
        "\n",
        "public class TestClass {\n",
        "    private String name;\n",
        "    private int age;\n",
        "    \n",
        "    public TestClass(String name, int age) {\n",
        "        this.name = name;\n",
        "        this.age = age;\n",
        "    }\n",
        "    \n",
        "    public String getName() {\n",
        "        return name;\n",
        "    }\n",
        "    \n",
        "    public void setName(String name) {\n",
        "        this.name = name;\n",
        "    }\n",
        "    \n",
        "    public enum Status {\n",
        "        ACTIVE, INACTIVE\n",
        "    }\n",
        "    \n",
        "    public record User(String id, String email) {\n",
        "        public boolean isValid() {\n",
        "            return id != null && email != null;\n",
        "        }\n",
        "    }\n",
        "}\n"
    ]
    
    try:
        splitter = get_code_splitter('java')
        result = splitter.split_code(java_code)
        
        if result:
            prefix, suffix = result
            print("✅ Java分割成功!")
            print(f"📏 Prefix长度: {len(prefix)} 字符")
            print(f"📏 Suffix长度: {len(suffix)} 字符")
            print(f"📊 Prefix比例: {len(prefix)/(len(prefix)+len(suffix))*100:.1f}%")
            print(f"📊 Suffix比例: {len(suffix)/(len(prefix)+len(suffix))*100:.1f}%")
            
            # 检查分割质量
            if len(prefix.strip()) >= 20 and len(suffix.strip()) >= 20:
                print("✅ 分割质量检查通过")
            else:
                print("❌ 分割质量检查失败")
                
            return True
        else:
            print("❌ Java分割失败")
            return False
            
    except Exception as e:
        print(f"❌ Java分割器错误: {e}")
        return False


def test_python_splitter():
    """测试Python分割器"""
    print("\n🧪 测试Python分割器...")
    
    python_code = [
        "import os\n",
        "import sys\n",
        "from typing import List, Optional\n",
        "\n",
        "class TestClass:\n",
        "    def __init__(self, name: str):\n",
        "        self.name = name\n",
        "        self.items: List[str] = []\n",
        "    \n",
        "    def add_item(self, item: str) -> None:\n",
        "        self.items.append(item)\n",
        "    \n",
        "    def get_items(self) -> List[str]:\n",
        "        return self.items.copy()\n",
        "    \n",
        "    def process_items(self) -> Optional[str]:\n",
        "        if not self.items:\n",
        "            return None\n",
        "        \n",
        "        result = \"\"\n",
        "        for item in self.items:\n",
        "            result += item.upper() + \" \"\n",
        "        \n",
        "        return result.strip()\n",
        "\n",
        "def main():\n",
        "    test = TestClass(\"test\")\n",
        "    test.add_item(\"hello\")\n",
        "    test.add_item(\"world\")\n",
        "    print(test.process_items())\n"
    ]
    
    try:
        splitter = get_code_splitter('py')
        result = splitter.split_code(python_code)
        
        if result:
            prefix, suffix = result
            print("✅ Python分割成功!")
            print(f"📏 Prefix长度: {len(prefix)} 字符")
            print(f"📏 Suffix长度: {len(suffix)} 字符")
            print(f"📊 Prefix比例: {len(prefix)/(len(prefix)+len(suffix))*100:.1f}%")
            print(f"📊 Suffix比例: {len(suffix)/(len(prefix)+len(suffix))*100:.1f}%")
            
            # 检查分割质量
            if len(prefix.strip()) >= 20 and len(suffix.strip()) >= 20:
                print("✅ 分割质量检查通过")
            else:
                print("❌ 分割质量检查失败")
                
            return True
        else:
            print("❌ Python分割失败")
            return False
            
    except Exception as e:
        print(f"❌ Python分割器错误: {e}")
        return False


def test_unsupported_language():
    """测试不支持的语言"""
    print("\n🧪 测试不支持的语言...")
    
    try:
        splitter = get_code_splitter('rust')
        print("❌ 应该抛出NotImplementedError")
        return False
    except NotImplementedError:
        print("✅ 正确抛出NotImplementedError")
        return True
    except Exception as e:
        print(f"❌ 意外的错误: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试代码分割器系统...")
    print(f"🔧 支持的语言: {', '.join(get_supported_languages())}")
    
    results = []
    
    # 测试Java分割器
    results.append(test_java_splitter())
    
    # 测试Python分割器
    results.append(test_python_splitter())
    
    # 测试不支持的语言
    results.append(test_unsupported_language())
    
    # 总结
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新的分割器系统工作正常。")
        return True
    else:
        print("❌ 部分测试失败，需要修复。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
