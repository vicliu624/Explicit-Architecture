#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
python_splitter.py
----------------------------------------------------
Python代码分割工具

功能：
1. 基于Python语法结构的智能代码分割
2. 支持类、函数、控制结构等边界检测
3. 保持代码语义完整性
4. 生成高质量的prefix/suffix对

依赖：
    Python 3.7+
    ast (标准库)
----------------------------------------------------
"""

import ast
import random
from typing import List, Tuple, Optional


class PythonCodeSplitter:
    """Python代码分割器"""
    
    def __init__(self):
        self.control_structures = {'if', 'for', 'while', 'try', 'with', 'def', 'class', 'async'}
    
    def split_code(self, lines: List[str]) -> Optional[Tuple[str, str]]:
        """
        分割Python代码为prefix和suffix
        
        Args:
            lines: 代码行列表
            
        Returns:
            (prefix, suffix) 元组，如果无法分割则返回None
        """
        if len(lines) < 4:
            return None
        
        content = "".join(lines)
        
        try:
            # 尝试解析AST
            tree = ast.parse(content)
            split_candidates = self._find_ast_split_points(tree, lines)
        except SyntaxError:
            # 如果AST解析失败，使用简单的行分割
            split_candidates = self._find_simple_split_points(lines)
        
        if not split_candidates:
            return None
        
        # 选择合适的分割点
        valid_splits = self._validate_splits(lines, split_candidates, content)
        
        if not valid_splits:
            return None
        
        # 随机选择一个有效的分割点
        split_point = random.choice(valid_splits)
        prefix = "".join(lines[:split_point])
        suffix = "".join(lines[split_point:])
        
        return prefix, suffix
    
    def _find_ast_split_points(self, tree: ast.AST, lines: List[str]) -> List[int]:
        """基于AST寻找分割点"""
        split_candidates = []
        
        class SplitPointFinder(ast.NodeVisitor):
            def __init__(self, lines):
                self.lines = lines
                self.split_points = []
            
            def visit_FunctionDef(self, node):
                # 函数定义开始
                if hasattr(node, 'lineno'):
                    self.split_points.append(node.lineno - 1)
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                # 类定义开始
                if hasattr(node, 'lineno'):
                    self.split_points.append(node.lineno - 1)
                self.generic_visit(node)
            
            def visit_If(self, node):
                # if语句开始
                if hasattr(node, 'lineno'):
                    self.split_points.append(node.lineno - 1)
                self.generic_visit(node)
            
            def visit_For(self, node):
                # for循环开始
                if hasattr(node, 'lineno'):
                    self.split_points.append(node.lineno - 1)
                self.generic_visit(node)
            
            def visit_While(self, node):
                # while循环开始
                if hasattr(node, 'lineno'):
                    self.split_points.append(node.lineno - 1)
                self.generic_visit(node)
            
            def visit_Try(self, node):
                # try语句开始
                if hasattr(node, 'lineno'):
                    self.split_points.append(node.lineno - 1)
                self.generic_visit(node)
        
        finder = SplitPointFinder(lines)
        finder.visit(tree)
        
        return finder.split_points
    
    def _find_simple_split_points(self, lines: List[str]) -> List[int]:
        """简单的行分割策略"""
        split_candidates = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 跳过空行和注释
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            # 检查是否是结构定义
            words = line_stripped.split()
            if words and words[0] in self.control_structures:
                split_candidates.append(i)
            
            # 检查是否是语句结束
            elif line_stripped.endswith(':'):
                split_candidates.append(i + 1)
        
        return split_candidates
    
    def _validate_splits(self, lines: List[str], split_candidates: List[int], content: str) -> List[int]:
        """验证分割点的有效性"""
        valid_splits = []
        
        for split_point in split_candidates:
            if 2 <= split_point <= len(lines) - 2:  # 确保前后都有内容
                prefix = "".join(lines[:split_point])
                suffix = "".join(lines[split_point:])
                
                # 验证分割质量
                if (len(prefix.strip()) >= 20 and len(suffix.strip()) >= 20 and
                    len(prefix) <= len(content) * 0.8 and  # prefix不超过80%
                    len(suffix) >= len(content) * 0.1):   # suffix至少10%
                    valid_splits.append(split_point)
        
        return valid_splits


# 工厂函数
def create_python_splitter() -> PythonCodeSplitter:
    """创建Python代码分割器实例"""
    return PythonCodeSplitter()


# 便捷函数
def split_python_code(lines: List[str]) -> Optional[Tuple[str, str]]:
    """
    便捷函数：分割Python代码
    
    Args:
        lines: 代码行列表
        
    Returns:
        (prefix, suffix) 元组，如果无法分割则返回None
    """
    splitter = create_python_splitter()
    return splitter.split_code(lines)


if __name__ == "__main__":
    # 测试代码
    test_lines = [
        "class TestClass:\n",
        "    def __init__(self, name):\n",
        "        self.name = name\n",
        "    \n",
        "    def get_name(self):\n",
        "        return self.name\n",
        "    \n",
        "    def set_name(self, name):\n",
        "        self.name = name\n"
    ]
    
    splitter = create_python_splitter()
    result = splitter.split_code(test_lines)
    
    if result:
        prefix, suffix = result
        print("Prefix:")
        print(prefix)
        print("\nSuffix:")
        print(suffix)
    else:
        print("无法分割代码")
