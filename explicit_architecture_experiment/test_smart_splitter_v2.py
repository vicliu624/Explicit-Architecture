#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_smart_splitter_v2.py
测试 SmartJavaSplitterV2 的功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import SmartJavaSplitterV2

def test_basic_functionality():
    """测试基本功能"""
    print("测试 SmartJavaSplitterV2 基本功能...")
    
    # 测试代码
    java_code = '''
package com.example;

import java.util.List;
import java.util.ArrayList;

public class UserService {
    private List<User> users;
    
    public UserService() {
        this.users = new ArrayList<>();
    }
    
    public void addUser(User user) {
        if (user != null) {
            users.add(user);
        }
    }
    
    public List<User> getAllUsers() {
        return new ArrayList<>(users);
    }
    
    public User findUserById(int id) {
        for (User user : users) {
            if (user.getId() == id) {
                return user;
            }
        }
        return null;
    }
}
'''
    
    # 创建分割器
    splitter = SmartJavaSplitterV2()
    
    # 测试基本分割
    print("测试基本分割...")
    results = splitter.split_file(java_code, mode='best')
    
    if results:
        result = results[0]
        print(f"分割成功!")
        print(f"   分割点: 第 {result.split_line} 行")
        print(f"   节点类型: {result.candidate.node_type}")
        print(f"   评分: {result.candidate.score:.4f}")
        print(f"   描述: {result.candidate.description}")
        print(f"   前缀长度: {len(result.prefix)} 字符")
        print(f"   后缀长度: {len(result.suffix)} 字符")
        
        # 显示分割结果预览
        print("\n前缀预览 (前200字符):")
        print(result.prefix[:200] + "..." if len(result.prefix) > 200 else result.prefix)
        
        print("\n后缀预览 (前200字符):")
        print(result.suffix[:200] + "..." if len(result.suffix) > 200 else result.suffix)
        
        return True
    else:
        print("分割失败")
        return False

def test_candidates_mode():
    """测试候选模式"""
    print("\n🧪 测试候选模式...")
    
    java_code = '''
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int subtract(int a, int b) {
        return a - b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
}
'''
    
    splitter = SmartJavaSplitterV2()
    results = splitter.split_file(java_code, mode='candidates')
    
    if results:
        print(f"✅ 找到 {len(results)} 个候选分割点:")
        for i, result in enumerate(results):
            print(f"   {i+1}. 第 {result.split_line} 行 - {result.candidate.node_type} (评分: {result.candidate.score:.4f})")
        return True
    else:
        print("❌ 未找到候选分割点")
        return False

def test_recursive_splitting():
    """测试递归分割"""
    print("\n🧪 测试递归分割...")
    
    java_code = '''
public class ComplexService {
    private DatabaseConnection db;
    
    public ComplexService() {
        this.db = new DatabaseConnection();
    }
    
    public void processData() {
        List<Data> data = fetchData();
        for (Data item : data) {
            processItem(item);
        }
        saveResults();
    }
    
    private List<Data> fetchData() {
        return db.query("SELECT * FROM data");
    }
    
    private void processItem(Data item) {
        // 处理逻辑
    }
    
    private void saveResults() {
        // 保存结果
    }
}
'''
    
    splitter = SmartJavaSplitterV2()
    results = splitter.split_file(java_code, mode='best', recursive=True)
    
    if results:
        print(f"✅ 递归分割成功，生成了 {len(results)} 个分割结果:")
        for i, result in enumerate(results):
            print(f"   {i+1}. 第 {result.split_line} 行 - {result.candidate.node_type} (评分: {result.candidate.score:.4f})")
        return True
    else:
        print("❌ 递归分割失败")
        return False

def test_scoring_parameters():
    """测试评分参数调整"""
    print("\n🧪 测试评分参数调整...")
    
    java_code = '''
public class TestClass {
    public void method1() {
        // 简单方法
    }
    
    public void method2() {
        // 另一个方法
    }
}
'''
    
    # 测试不同的评分参数
    scoring_configs = [
        {'alpha_semantic': 1.0, 'beta_balance': 1.0, 'gamma_density': 0.5, 'delta_depth': 0.3},
        {'alpha_semantic': 2.0, 'beta_balance': 0.5, 'gamma_density': 0.3, 'delta_depth': 0.2},
        {'alpha_semantic': 0.5, 'beta_balance': 2.0, 'gamma_density': 1.0, 'delta_depth': 0.5},
    ]
    
    for i, config in enumerate(scoring_configs):
        print(f"   配置 {i+1}: {config}")
        splitter = SmartJavaSplitterV2(scoring_params=config)
        results = splitter.split_file(java_code, mode='candidates')
        
        if results:
            best = max(results, key=lambda x: x.candidate.score)
            print(f"     最佳分割: 第 {best.split_line} 行, 评分: {best.candidate.score:.4f}")
        else:
            print("     无分割结果")

def test_validation():
    """测试验证功能"""
    print("\n🧪 测试验证功能...")
    
    # 测试有问题的代码（括号不匹配）
    bad_code = '''
public class BadClass {
    public void method() {
        if (true) {
            // 缺少闭合括号
        }
    }
    // 这里应该有闭合括号
'''
    
    splitter = SmartJavaSplitterV2()
    results = splitter.split_file(bad_code, mode='best')
    
    if results:
        print("✅ 分割成功（验证器允许了不完美的代码）")
        return True
    else:
        print("❌ 分割失败（验证器拒绝了有问题的代码）")
        return False

def main():
    """主测试函数"""
    print("开始测试 SmartJavaSplitterV2")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_candidates_mode,
        test_recursive_splitting,
        test_scoring_parameters,
        test_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("所有测试通过！SmartJavaSplitterV2 工作正常")
    else:
        print("部分测试失败，请检查实现")

if __name__ == "__main__":
    main()
