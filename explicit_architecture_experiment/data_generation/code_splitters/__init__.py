#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code_splitters package
----------------------------------------------------
代码分割器包

功能：
1. 提供各种编程语言的代码分割器
2. 统一的接口和工厂模式
3. 支持扩展新的语言

支持的语言：
- Java (java_splitter.py)
- Python (python_splitter.py) - 待实现
- JavaScript/TypeScript (js_splitter.py) - 待实现
- C++ (cpp_splitter.py) - 待实现
- C# (csharp_splitter.py) - 待实现
- Go (go_splitter.py) - 待实现
- Rust (rust_splitter.py) - 待实现

依赖：
    Python 3.7+
----------------------------------------------------
"""

from typing import List, Tuple, Optional, Dict, Type
from .java_splitter import JavaCodeSplitter, create_java_splitter
from .python_splitter import PythonCodeSplitter, create_python_splitter
from .smart_java_splitter_v2 import SmartJavaSplitterV2


class CodeSplitterFactory:
    """代码分割器工厂"""
    
    def __init__(self):
        self._splitters: Dict[str, Type] = {
            'java': JavaCodeSplitter,
            'py': PythonCodeSplitter,  # Python分割器已实现
            'js': None,  # JavaScript分割器待实现
            'ts': None,  # TypeScript分割器待实现
            'cpp': None,  # C++分割器待实现
            'c': None,    # C分割器待实现
            'cs': None,   # C#分割器待实现
            'go': None,   # Go分割器待实现
            'rs': None,   # Rust分割器待实现
        }
    
    def get_splitter(self, language: str):
        """获取指定语言的分割器"""
        if language not in self._splitters:
            raise ValueError(f"不支持的语言: {language}")
        
        splitter_class = self._splitters[language]
        if splitter_class is None:
            raise NotImplementedError(f"{language} 分割器尚未实现")
        
        return splitter_class()
    
    def register_splitter(self, language: str, splitter_class: Type):
        """注册新的分割器"""
        self._splitters[language] = splitter_class
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return [lang for lang, splitter in self._splitters.items() if splitter is not None]


# 全局工厂实例
_factory = CodeSplitterFactory()


def get_code_splitter(language: str):
    """获取代码分割器"""
    return _factory.get_splitter(language)


def split_code(lines: List[str], language: str) -> Optional[Tuple[str, str]]:
    """
    便捷函数：分割代码
    
    Args:
        lines: 代码行列表
        language: 编程语言
        
    Returns:
        (prefix, suffix) 元组，如果无法分割则返回None
    """
    splitter = get_code_splitter(language)
    return splitter.split_code(lines)


def get_supported_languages() -> List[str]:
    """获取支持的语言列表"""
    return _factory.get_supported_languages()


# 向后兼容的便捷函数
def create_java_splitter():
    """创建Java代码分割器（向后兼容）"""
    return create_java_splitter()


__all__ = [
    'CodeSplitterFactory',
    'get_code_splitter',
    'split_code',
    'get_supported_languages',
    'create_java_splitter',
    'create_python_splitter',
    'JavaCodeSplitter',
    'PythonCodeSplitter',
    'SmartJavaSplitterV2'
]
