#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_integration.py
测试 SmartJavaSplitterV2 与 direct_data_builder.py 的集成
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.direct_data_builder import make_completion_samples

def create_test_java_project():
    """创建一个测试Java项目"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    project_dir = os.path.join(temp_dir, "test_java_project")
    os.makedirs(project_dir, exist_ok=True)
    
    # 创建测试Java文件
    java_files = [
        {
            "name": "UserService.java",
            "content": '''
package com.example.service;

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
        },
        {
            "name": "User.java",
            "content": '''
package com.example.model;

public class User {
    private int id;
    private String name;
    private String email;
    
    public User(int id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
    }
    
    public int getId() {
        return id;
    }
    
    public String getName() {
        return name;
    }
    
    public String getEmail() {
        return email;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public void setEmail(String email) {
        this.email = email;
    }
}
'''
        }
    ]
    
    # 写入文件
    for file_info in java_files:
        file_path = os.path.join(project_dir, file_info["name"])
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_info["content"])
    
    return project_dir

def test_integration():
    """测试集成功能"""
    print("开始测试 SmartJavaSplitterV2 集成...")
    
    # 创建测试项目
    project_dir = create_test_java_project()
    print(f"创建测试项目: {project_dir}")
    
    try:
        # 测试生成补全样本
        print("测试生成补全样本...")
        samples = make_completion_samples(project_dir, "explicit")
        
        print(f"生成了 {len(samples)} 个样本")
        
        # 检查样本质量
        for i, sample in enumerate(samples):
            print(f"\n样本 {i+1}:")
            print(f"  文件: {sample['file']}")
            print(f"  语言: {sample['language']}")
            print(f"  视图: {sample['view']}")
            
            # 检查是否有SmartJavaSplitterV2的额外信息
            if 'split_line' in sample:
                print(f"  分割行: {sample['split_line']}")
                print(f"  分割评分: {sample['split_score']:.4f}")
                print(f"  分割类型: {sample['split_type']}")
                print(f"  分割描述: {sample['split_description']}")
            
            print(f"  前缀长度: {len(sample['prefix'])} 字符")
            print(f"  后缀长度: {len(sample['suffix'])} 字符")
            
            # 显示分割结果预览
            print("  前缀预览 (前100字符):")
            print(f"    {sample['prefix'][:100]}...")
            print("  后缀预览 (前100字符):")
            print(f"    {sample['suffix'][:100]}...")
        
        return len(samples) > 0
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    finally:
        # 清理临时目录
        shutil.rmtree(project_dir, ignore_errors=True)
        shutil.rmtree(os.path.dirname(project_dir), ignore_errors=True)

def main():
    """主测试函数"""
    print("=" * 60)
    print("测试 SmartJavaSplitterV2 与 direct_data_builder.py 的集成")
    print("=" * 60)
    
    success = test_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("集成测试通过！SmartJavaSplitterV2 成功集成到 direct_data_builder.py")
    else:
        print("集成测试失败！")
    print("=" * 60)

if __name__ == "__main__":
    main()
