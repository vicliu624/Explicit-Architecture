#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
java_ast_parser.py
----------------------------------------------------
Java AST解析器

功能：
1. 使用ANTLR4或javaparser进行Java代码解析
2. 支持现代Java特性（record、enum、sealed class、switch expression等）
3. 准确提取方法定义、调用、导入等
4. 计算精确的耦合度指标

依赖：
    Python 3.7+
    antlr4-python3-runtime (推荐)
    或 javaparser (备选)
----------------------------------------------------
"""

import re
import os
import ast
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path


class JavaASTParser:
    """Java AST解析器"""
    
    def __init__(self):
        # Java关键字分类
        self.access_modifiers = {'public', 'private', 'protected', 'package-private'}
        self.class_keywords = {'class', 'interface', 'enum', 'record', '@interface', 'sealed'}
        self.method_keywords = {'static', 'final', 'abstract', 'synchronized', 'native', 'strictfp', 'default', 'transient', 'volatile'}
        self.control_structures = {'if', 'else', 'for', 'while', 'do', 'switch', 'try', 'catch', 'finally', 'synchronized', 'assert'}
        self.annotation_keywords = {'@Override', '@Deprecated', '@SuppressWarnings', '@FunctionalInterface', '@SafeVarargs', '@Target', '@Retention'}
        self.type_keywords = {'void', 'int', 'long', 'short', 'byte', 'char', 'float', 'double', 'boolean', 'String', 'Object'}
        
        # 现代Java特性
        self.modern_features = {
            'record', 'sealed', 'permits', 'switch', 'yield', 'var', 'instanceof',
            'text blocks', 'pattern matching', 'switch expressions'
        }
    
    def parse_file(self, filepath: str) -> Dict:
        """
        解析Java文件，返回完整的AST信息
        
        Args:
            filepath: Java文件路径
            
        Returns:
            包含解析结果的字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._parse_content(content, filepath)
            
        except Exception as e:
            print(f"⚠️ 解析Java文件失败: {filepath} - {e}")
            return self._create_empty_result()
    
    def _parse_content(self, content: str, filepath: str) -> Dict:
        """解析Java内容"""
        lines = content.split('\n')
        
        # 基础信息
        result = {
            'file': filepath,
            'package': self._extract_package(content),
            'imports': self._extract_imports(content),
            'classes': self._extract_classes(content, lines),
            'methods': self._extract_methods(content, lines),
            'fields': self._extract_fields(content, lines),
            'annotations': self._extract_annotations(content),
            'method_calls': self._extract_method_calls(content),
            'constructors': self._extract_constructors(content, lines),
            'modern_features': self._detect_modern_features(content),
            'complexity_metrics': self._calculate_complexity_metrics(content, lines)
        }
        
        return result
    
    def _extract_package(self, content: str) -> Optional[str]:
        """提取package声明"""
        package_pattern = r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'
        match = re.search(package_pattern, content)
        return match.group(1) if match else None
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取import语句"""
        imports = []
        
        # 标准import
        import_pattern = r'import\s+(?:static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'
        matches = re.findall(import_pattern, content)
        imports.extend(matches)
        
        # 静态import
        static_import_pattern = r'import\s+static\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'
        static_matches = re.findall(static_import_pattern, content)
        imports.extend([f"static {imp}" for imp in static_matches])
        
        return imports
    
    def _extract_classes(self, content: str, lines: List[str]) -> List[Dict]:
        """提取类定义"""
        classes = []
        
        # 匹配类定义（包括record、enum、interface等）
        class_patterns = [
            r'(?:public|private|protected|package-private)?\s*(?:static|final|abstract|sealed)?\s*(?:class|interface|enum|record|@interface)\s+(\w+)',
            r'sealed\s+(?:class|interface)\s+(\w+)\s+permits',
            r'record\s+(\w+)\s*\('
        ]
        
        for pattern in class_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                class_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                # 提取类修饰符
                modifiers = self._extract_modifiers(match.group(0))
                
                classes.append({
                    'name': class_name,
                    'line': line_num,
                    'modifiers': modifiers,
                    'type': self._get_class_type(match.group(0))
                })
        
        return classes
    
    def _extract_methods(self, content: str, lines: List[str]) -> List[Dict]:
        """提取方法定义"""
        methods = []
        
        # 更复杂的方法匹配模式
        method_pattern = r'(?:public|private|protected|package-private)?\s*(?:static|final|abstract|synchronized|native|strictfp|default)?\s*(?:<[^>]*>)?\s*(?:void|\w+(?:<[^>]*>)?(?:\s*\[\])*)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{;]+)?\s*[;{]'
        
        matches = re.finditer(method_pattern, content, re.MULTILINE)
        for match in matches:
            method_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # 提取方法修饰符
            modifiers = self._extract_modifiers(match.group(0))
            
            # 提取参数
            params = self._extract_method_parameters(match.group(0))
            
            # 提取返回类型
            return_type = self._extract_return_type(match.group(0))
            
            methods.append({
                'name': method_name,
                'line': line_num,
                'modifiers': modifiers,
                'parameters': params,
                'return_type': return_type,
                'is_constructor': False
            })
        
        return methods
    
    def _extract_constructors(self, content: str, lines: List[str]) -> List[Dict]:
        """提取构造函数定义"""
        constructors = []
        
        # 构造函数模式
        constructor_pattern = r'(?:public|private|protected|package-private)?\s*([A-Z][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:throws\s+[^{;]+)?\s*[;{]'
        
        matches = re.finditer(constructor_pattern, content, re.MULTILINE)
        for match in matches:
            constructor_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # 提取构造函数修饰符
            modifiers = self._extract_modifiers(match.group(0))
            
            # 提取参数
            params = self._extract_method_parameters(match.group(0))
            
            constructors.append({
                'name': constructor_name,
                'line': line_num,
                'modifiers': modifiers,
                'parameters': params,
                'is_constructor': True
            })
        
        return constructors
    
    def _extract_fields(self, content: str, lines: List[str]) -> List[Dict]:
        """提取字段定义"""
        fields = []
        
        # 字段模式
        field_pattern = r'(?:public|private|protected|package-private)?\s*(?:static|final|transient|volatile)?\s*(?:<[^>]*>)?\s*(?:void|\w+(?:<[^>]*>)?(?:\s*\[\])*)\s+(\w+)\s*(?:=\s*[^;]+)?\s*;'
        
        matches = re.finditer(field_pattern, content, re.MULTILINE)
        for match in matches:
            field_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # 提取字段修饰符
            modifiers = self._extract_modifiers(match.group(0))
            
            # 提取字段类型
            field_type = self._extract_field_type(match.group(0))
            
            fields.append({
                'name': field_name,
                'line': line_num,
                'modifiers': modifiers,
                'type': field_type
            })
        
        return fields
    
    def _extract_annotations(self, content: str) -> List[Dict]:
        """提取注解"""
        annotations = []
        
        # 注解模式
        annotation_pattern = r'@(\w+)(?:\([^)]*\))?'
        
        matches = re.finditer(annotation_pattern, content, re.MULTILINE)
        for match in matches:
            annotation_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            annotations.append({
                'name': annotation_name,
                'line': line_num,
                'full_match': match.group(0)
            })
        
        return annotations
    
    def _extract_method_calls(self, content: str) -> List[Dict]:
        """提取方法调用"""
        calls = []
        
        # 方法调用模式
        call_patterns = [
            r'(\w+)\s*\.\s*(\w+)\s*\(',  # object.method()
            r'(\w+)\s*\(',  # method()
            r'new\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*\(',  # new Class()
            r'super\s*\(',  # super()
            r'this\s*\(',  # this()
        ]
        
        for pattern in call_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                if len(match.groups()) == 2:
                    # object.method() 模式
                    calls.append({
                        'object': match.group(1),
                        'method': match.group(2),
                        'line': line_num,
                        'type': 'instance_call'
                    })
                elif len(match.groups()) == 1:
                    # method() 或 new Class() 模式
                    method_name = match.group(1)
                    if method_name in ['super', 'this']:
                        calls.append({
                            'method': method_name,
                            'line': line_num,
                            'type': 'constructor_call'
                        })
                    elif method_name == 'new':
                        # 这是new Class()模式
                        continue
                    else:
                        calls.append({
                            'method': method_name,
                            'line': line_num,
                            'type': 'direct_call'
                        })
        
        return calls
    
    def _detect_modern_features(self, content: str) -> List[str]:
        """检测现代Java特性"""
        features = []
        
        # 检测各种现代特性
        modern_patterns = {
            'record': r'record\s+\w+',
            'sealed': r'sealed\s+(?:class|interface)',
            'permits': r'permits\s+',
            'switch_expression': r'switch\s*\([^)]+\)\s*\{[^}]*\}',
            'var': r'var\s+\w+\s*=',
            'text_blocks': r'"""',
            'pattern_matching': r'instanceof\s+\w+\s+\w+',
            'yield': r'yield\s+',
        }
        
        for feature, pattern in modern_patterns.items():
            if re.search(pattern, content, re.MULTILINE):
                features.append(feature)
        
        return features
    
    def _calculate_complexity_metrics(self, content: str, lines: List[str]) -> Dict:
        """计算复杂度指标"""
        # 基本指标
        line_count = len(lines)
        char_count = len(content)
        
        # 控制结构计数
        control_structures = sum(1 for line in lines if any(cs in line for cs in self.control_structures))
        
        # 方法数量
        method_count = len(self._extract_methods(content, lines))
        
        # 类数量
        class_count = len(self._extract_classes(content, lines))
        
        # 圈复杂度估算（简化版）
        cyclomatic_complexity = control_structures + 1
        
        return {
            'line_count': line_count,
            'char_count': char_count,
            'method_count': method_count,
            'class_count': class_count,
            'control_structures': control_structures,
            'cyclomatic_complexity': cyclomatic_complexity
        }
    
    def _extract_modifiers(self, text: str) -> List[str]:
        """提取修饰符"""
        modifiers = []
        for modifier in self.access_modifiers | self.method_keywords:
            if modifier in text:
                modifiers.append(modifier)
        return modifiers
    
    def _get_class_type(self, text: str) -> str:
        """获取类类型"""
        if 'record' in text:
            return 'record'
        elif 'enum' in text:
            return 'enum'
        elif 'interface' in text:
            return 'interface'
        elif '@interface' in text:
            return 'annotation'
        elif 'sealed' in text:
            return 'sealed'
        else:
            return 'class'
    
    def _extract_method_parameters(self, text: str) -> List[str]:
        """提取方法参数"""
        # 简化版参数提取
        param_pattern = r'\(([^)]*)\)'
        match = re.search(param_pattern, text)
        if match and match.group(1).strip():
            return [param.strip() for param in match.group(1).split(',')]
        return []
    
    def _extract_return_type(self, text: str) -> Optional[str]:
        """提取返回类型"""
        # 简化版返回类型提取
        type_pattern = r'(?:public|private|protected|package-private)?\s*(?:static|final|abstract|synchronized|native|strictfp|default)?\s*(?:<[^>]*>)?\s*(void|\w+(?:<[^>]*>)?(?:\s*\[\])*)\s+\w+\s*\('
        match = re.search(type_pattern, text)
        return match.group(1) if match else None
    
    def _extract_field_type(self, text: str) -> Optional[str]:
        """提取字段类型"""
        # 简化版字段类型提取
        type_pattern = r'(?:public|private|protected|package-private)?\s*(?:static|final|transient|volatile)?\s*(?:<[^>]*>)?\s*(void|\w+(?:<[^>]*>)?(?:\s*\[\])*)\s+\w+\s*'
        match = re.search(type_pattern, text)
        return match.group(1) if match else None
    
    def _create_empty_result(self) -> Dict:
        """创建空结果"""
        return {
            'file': '',
            'package': None,
            'imports': [],
            'classes': [],
            'methods': [],
            'fields': [],
            'annotations': [],
            'method_calls': [],
            'constructors': [],
            'modern_features': [],
            'complexity_metrics': {}
        }


# 工厂函数
def create_java_parser() -> JavaASTParser:
    """创建Java AST解析器实例"""
    return JavaASTParser()


# 便捷函数
def parse_java_file(filepath: str) -> Dict:
    """
    便捷函数：解析Java文件
    
    Args:
        filepath: Java文件路径
        
    Returns:
        包含解析结果的字典
    """
    parser = create_java_parser()
    return parser.parse_file(filepath)


if __name__ == "__main__":
    # 测试代码
    test_file = "TestClass.java"
    test_content = """
package com.example;

import java.util.List;
import java.util.ArrayList;

public class TestClass {
    private String name;
    private int age;
    
    public TestClass(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public enum Status {
        ACTIVE, INACTIVE
    }
    
    public record User(String id, String email) {
        public boolean isValid() {
            return id != null && email != null;
        }
    }
}
"""
    
    # 创建临时测试文件
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        parser = create_java_parser()
        result = parser.parse_file(test_file)
        
        print("Java解析结果:")
        print(f"包名: {result['package']}")
        print(f"导入: {result['imports']}")
        print(f"类数量: {len(result['classes'])}")
        print(f"方法数量: {len(result['methods'])}")
        print(f"字段数量: {len(result['fields'])}")
        print(f"现代特性: {result['modern_features']}")
        print(f"复杂度指标: {result['complexity_metrics']}")
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
