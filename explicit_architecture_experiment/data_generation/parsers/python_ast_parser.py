#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
python_ast_parser.py
----------------------------------------------------
Python AST解析器

功能：
1. 使用标准库ast进行Python代码解析
2. 提取类、函数、导入等信息
3. 计算复杂度指标

依赖：
    Python 3.7+
    ast (标准库)
----------------------------------------------------
"""

import ast
import os
from typing import List, Dict, Optional


class PythonASTParser:
    """Python AST解析器"""
    
    def __init__(self):
        self.control_structures = {'if', 'for', 'while', 'try', 'with', 'def', 'class', 'async'}
    
    def parse_file(self, filepath: str) -> Dict:
        """
        解析Python文件，返回完整的AST信息
        
        Args:
            filepath: Python文件路径
            
        Returns:
            包含解析结果的字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._parse_content(content, filepath)
            
        except Exception as e:
            print(f"⚠️ 解析Python文件失败: {filepath} - {e}")
            return self._create_empty_result()
    
    def _parse_content(self, content: str, filepath: str) -> Dict:
        """解析Python内容"""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"⚠️ Python语法错误: {filepath} - {e}")
            return self._create_empty_result()
        
        lines = content.split('\n')
        
        # 基础信息
        result = {
            'file': filepath,
            'imports': self._extract_imports(tree),
            'classes': self._extract_classes(tree, lines),
            'functions': self._extract_functions(tree, lines),
            'function_calls': self._extract_function_calls(tree, lines),
            'complexity_metrics': self._calculate_complexity_metrics(tree, lines)
        }
        
        return result
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """提取导入语句"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    
    def _extract_classes(self, tree: ast.AST, lines: List[str]) -> List[Dict]:
        """提取类定义"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [ast.unparse(base) for base in node.bases],
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list]
                })
        
        return classes
    
    def _extract_functions(self, tree: ast.AST, lines: List[str]) -> List[Dict]:
        """提取函数定义"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list]
                })
        
        return functions
    
    def _extract_function_calls(self, tree: ast.AST, lines: List[str]) -> List[Dict]:
        """提取函数调用"""
        calls = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append({
                        'function': node.func.id,
                        'line': node.lineno,
                        'type': 'direct_call'
                    })
                elif isinstance(node.func, ast.Attribute):
                    calls.append({
                        'object': ast.unparse(node.func.value),
                        'function': node.func.attr,
                        'line': node.lineno,
                        'type': 'method_call'
                    })
        
        return calls
    
    def _calculate_complexity_metrics(self, tree: ast.AST, lines: List[str]) -> Dict:
        """计算复杂度指标"""
        # 基本指标
        line_count = len(lines)
        char_count = sum(len(line) for line in lines)
        
        # 控制结构计数
        control_structures = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                control_structures += 1
        
        # 函数和类数量
        function_count = len(self._extract_functions(tree, lines))
        class_count = len(self._extract_classes(tree, lines))
        
        # 圈复杂度估算
        cyclomatic_complexity = control_structures + 1
        
        return {
            'line_count': line_count,
            'char_count': char_count,
            'function_count': function_count,
            'class_count': class_count,
            'control_structures': control_structures,
            'cyclomatic_complexity': cyclomatic_complexity
        }
    
    def _create_empty_result(self) -> Dict:
        """创建空结果"""
        return {
            'file': '',
            'imports': [],
            'classes': [],
            'functions': [],
            'function_calls': [],
            'complexity_metrics': {}
        }


# 工厂函数
def create_python_parser() -> PythonASTParser:
    """创建Python AST解析器实例"""
    return PythonASTParser()


# 便捷函数
def parse_python_file(filepath: str) -> Dict:
    """
    便捷函数：解析Python文件
    
    Args:
        filepath: Python文件路径
        
    Returns:
        包含解析结果的字典
    """
    parser = create_python_parser()
    return parser.parse_file(filepath)


if __name__ == "__main__":
    # 测试代码
    test_file = "test_module.py"
    test_content = """
import os
import sys
from typing import List, Optional

class TestClass:
    def __init__(self, name: str):
        self.name = name
        self.items: List[str] = []
    
    def add_item(self, item: str) -> None:
        self.items.append(item)
    
    def get_items(self) -> List[str]:
        return self.items.copy()
    
    def process_items(self) -> Optional[str]:
        if not self.items:
            return None
        
        result = ""
        for item in self.items:
            result += item.upper() + " "
        
        return result.strip()

def main():
    test = TestClass("test")
    test.add_item("hello")
    test.add_item("world")
    print(test.process_items())
"""
    
    # 创建临时测试文件
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        parser = create_python_parser()
        result = parser.parse_file(test_file)
        
        print("Python解析结果:")
        print(f"导入: {result['imports']}")
        print(f"类数量: {len(result['classes'])}")
        print(f"函数数量: {len(result['functions'])}")
        print(f"函数调用数量: {len(result['function_calls'])}")
        print(f"复杂度指标: {result['complexity_metrics']}")
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
