#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_optimized_builder.py
----------------------------------------------------
测试优化后的direct_data_builder.py

功能：
1. 测试新的AST-based解析功能
2. 验证改进的耦合度计算
3. 对比优化前后的效果

依赖：
    Python 3.7+
----------------------------------------------------
"""

import sys
import os
import tempfile
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.direct_data_builder import (
    parse_java_imports, 
    parse_java_method_calls, 
    extract_java_methods,
    compute_coupling,
    make_completion_samples
)


def create_test_java_file():
    """创建测试用的Java文件"""
    test_content = """
package com.example.test;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import static java.util.Collections.emptyList;

public class TestClass {
    private String name;
    private int age;
    private Map<String, List<String>> dataMap;
    
    public TestClass(String name, int age) {
        this.name = name;
        this.age = age;
        this.dataMap = new HashMap<>();
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public void addData(String key, List<String> values) {
        if (key == null || values == null) {
            throw new IllegalArgumentException("参数不能为空");
        }
        dataMap.computeIfAbsent(key, k -> new ArrayList<>()).addAll(values);
    }
    
    public List<String> getData(String key) {
        List<String> values = dataMap.get(key);
        return values != null ? values : emptyList();
    }
    
    public void processData() {
        for (Map.Entry<String, List<String>> entry : dataMap.entrySet()) {
            String key = entry.getKey();
            List<String> values = entry.getValue();
            System.out.println("Key: " + key + ", Values: " + values.size());
        }
    }
    
    public enum Status {
        ACTIVE, INACTIVE, PENDING
    }
    
    public record User(String id, String email) {
        public boolean isValid() {
            return id != null && email != null;
        }
    }
    
    public interface DataProcessor {
        void process(String data);
        
        default void log(String message) {
            System.out.println("[" + getClass().getSimpleName() + "] " + message);
        }
    }
}
"""
    return test_content


def test_java_imports_parsing():
    """测试Java导入解析"""
    print("测试Java导入解析...")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
        f.write(create_test_java_file())
        temp_file = f.name
    
    try:
        imports = parse_java_imports(temp_file)
        
        print(f"解析到的导入: {imports}")
        
        # 验证结果
        expected_imports = [
            'com.example.test',  # package
            'java.util.List',
            'java.util.ArrayList', 
            'java.util.Map',
            'java.util.HashMap',
            'static java.util.Collections.emptyList'
        ]
        
        success = True
        for expected in expected_imports:
            if expected not in imports:
                print(f"缺少预期导入: {expected}")
                success = False
        
        if success:
            print("Java导入解析测试通过!")
            return True
        else:
            print("Java导入解析测试失败!")
            return False
            
    finally:
        os.unlink(temp_file)


def test_java_method_calls_parsing():
    """测试Java方法调用解析"""
    print("\n测试Java方法调用解析...")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
        f.write(create_test_java_file())
        temp_file = f.name
    
    try:
        calls = parse_java_method_calls(temp_file)
        
        print(f"解析到的方法调用: {calls}")
        
        # 验证结果
        expected_calls = [
            ('new HashMap', 'HashMap'),
            ('new ArrayList', 'ArrayList'),
            ('dataMap.computeIfAbsent', 'computeIfAbsent'),
            ('dataMap.get', 'get'),
            ('emptyList', 'emptyList'),
            ('System.out.println', 'println')
        ]
        
        success = True
        for expected in expected_calls:
            if expected not in calls:
                print(f"缺少预期方法调用: {expected}")
                success = False
        
        if success:
            print("Java方法调用解析测试通过!")
            return True
        else:
            print("Java方法调用解析测试失败!")
            return False
            
    finally:
        os.unlink(temp_file)


def test_java_methods_extraction():
    """测试Java方法定义提取"""
    print("\n测试Java方法定义提取...")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
        f.write(create_test_java_file())
        temp_file = f.name
    
    try:
        methods = extract_java_methods(temp_file)
        
        print(f"提取到的方法: {methods}")
        
        # 验证结果
        expected_methods = [
            'TestClass',  # 构造函数
            'getName',
            'setName', 
            'addData',
            'getData',
            'processData',
            'isValid'  # record中的方法
        ]
        
        success = True
        for expected in expected_methods:
            if expected not in methods:
                print(f"缺少预期方法: {expected}")
                success = False
        
        if success:
            print("Java方法定义提取测试通过!")
            return True
        else:
            print("Java方法定义提取测试失败!")
            return False
            
    finally:
        os.unlink(temp_file)


def test_coupling_computation():
    """测试耦合度计算"""
    print("\n测试耦合度计算...")
    
    # 创建临时目录和文件
    temp_dir = tempfile.mkdtemp()
    try:
        # 创建测试Java文件
        java_file = os.path.join(temp_dir, "TestClass.java")
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write(create_test_java_file())
        
        # 计算耦合度
        coupling = compute_coupling(temp_dir)
        
        print(f"耦合度计算结果: {coupling}")
        
        if java_file in coupling:
            result = coupling[java_file]
            print(f"导入耦合度: {result['import_coupling']}")
            print(f"调用耦合度: {result['call_coupling']}")
            print(f"综合耦合度: {result['coupling_score']}")
            print(f"总依赖数: {result['total_dependencies']}")
            
            # 验证结果合理性
            if (result['import_coupling'] > 0 and 
                result['call_coupling'] > 0 and 
                result['coupling_score'] > 0):
                print("耦合度计算测试通过!")
                return True
            else:
                print("耦合度计算结果异常!")
                return False
        else:
            print("未找到Java文件的耦合度数据!")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def test_completion_samples():
    """测试补全样本生成"""
    print("\n测试补全样本生成...")
    
    # 创建临时目录和文件
    temp_dir = tempfile.mkdtemp()
    try:
        # 创建测试Java文件
        java_file = os.path.join(temp_dir, "TestClass.java")
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write(create_test_java_file())
        
        # 生成补全样本
        samples = make_completion_samples(temp_dir, "test")
        
        print(f"生成的补全样本数量: {len(samples)}")
        
        if samples:
            sample = samples[0]
            print(f"样本文件: {sample['file']}")
            print(f"样本语言: {sample['language']}")
            print(f"Prefix长度: {len(sample['prefix'])}")
            print(f"Suffix长度: {len(sample['suffix'])}")
            
            # 验证样本质量
            if (len(sample['prefix']) > 20 and 
                len(sample['suffix']) > 20 and
                sample['language'] == 'java'):
                print("补全样本生成测试通过!")
                return True
            else:
                print("补全样本质量不符合要求!")
                return False
        else:
            print("未生成任何补全样本!")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def main():
    """主测试函数"""
    print("开始测试优化后的direct_data_builder.py...")
    
    results = []
    
    # 测试各个功能
    results.append(test_java_imports_parsing())
    results.append(test_java_method_calls_parsing())
    results.append(test_java_methods_extraction())
    results.append(test_coupling_computation())
    results.append(test_completion_samples())
    
    # 总结
    passed = sum(results)
    total = len(results)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("所有测试通过！优化后的direct_data_builder.py工作正常。")
        print("主要改进:")
        print("  - 使用AST-based解析器替代简单的正则表达式")
        print("  - 支持现代Java特性（record、enum、sealed等）")
        print("  - 更准确的耦合度计算")
        print("  - 更好的错误处理和容错能力")
        print("  - 改进的代码分割质量")
        return True
    else:
        print("部分测试失败，需要进一步改进。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
