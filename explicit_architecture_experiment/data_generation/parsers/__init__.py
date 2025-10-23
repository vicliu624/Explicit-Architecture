#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsers package
----------------------------------------------------
代码解析器包

功能：
1. 提供各种编程语言的AST解析器
2. 支持现代语言特性
3. 统一的接口和工厂模式
4. 支持扩展新的语言

支持的语言：
- Java (java_ast_parser.py) - 使用ANTLR4或javaparser
- Python (python_ast_parser.py) - 使用标准库ast
- JavaScript/TypeScript (js_ast_parser.py) - 使用tree-sitter
- C++ (cpp_ast_parser.py) - 使用tree-sitter
- C# (csharp_ast_parser.py) - 使用tree-sitter
- Go (go_ast_parser.py) - 使用tree-sitter
- Rust (rust_ast_parser.py) - 使用tree-sitter

依赖：
    Python 3.7+
    tree-sitter (可选，用于多语言支持)
    antlr4-python3-runtime (可选，用于Java)
----------------------------------------------------
"""

from typing import List, Tuple, Optional, Dict, Type
from .java_ast_parser import JavaASTParser, create_java_parser
from .python_ast_parser import PythonASTParser, create_python_parser


class ParserFactory:
    """解析器工厂"""
    
    def __init__(self):
        self._parsers: Dict[str, Type] = {
            'java': JavaASTParser,
            'py': PythonASTParser,  # Python解析器已实现
            'js': None,  # JavaScript解析器待实现
            'ts': None,  # TypeScript解析器待实现
            'cpp': None,  # C++解析器待实现
            'c': None,    # C解析器待实现
            'cs': None,   # C#解析器待实现
            'go': None,   # Go解析器待实现
            'rs': None,   # Rust解析器待实现
        }
    
    def get_parser(self, language: str):
        """获取指定语言的解析器"""
        if language not in self._parsers:
            raise ValueError(f"不支持的语言: {language}")
        
        parser_class = self._parsers[language]
        if parser_class is None:
            raise NotImplementedError(f"{language} 解析器尚未实现")
        
        return parser_class()
    
    def register_parser(self, language: str, parser_class: Type):
        """注册新的解析器"""
        self._parsers[language] = parser_class
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return [lang for lang, parser in self._parsers.items() if parser is not None]


# 全局工厂实例
_factory = ParserFactory()


def get_parser(language: str):
    """获取解析器"""
    return _factory.get_parser(language)


def get_supported_languages() -> List[str]:
    """获取支持的语言列表"""
    return _factory.get_supported_languages()


# 向后兼容的便捷函数
def create_java_parser():
    """创建Java解析器（向后兼容）"""
    return create_java_parser()


def create_python_parser():
    """创建Python解析器（向后兼容）"""
    return create_python_parser()


__all__ = [
    'ParserFactory',
    'get_parser',
    'get_supported_languages',
    'create_java_parser',
    'create_python_parser',
    'JavaASTParser',
    'PythonASTParser'
]
