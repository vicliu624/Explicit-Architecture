#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple_test_v2.py
简化测试 SmartJavaSplitterV2
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import SmartJavaSplitterV2

def main():
    print("Testing SmartJavaSplitterV2...")
    
    # 测试代码
    java_code = '''
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
}
'''
    
    # 创建分割器
    splitter = SmartJavaSplitterV2()
    
    # 测试基本分割
    print("Testing basic split...")
    results = splitter.split_file(java_code, mode='best')
    
    if results:
        result = results[0]
        print(f"Split successful!")
        print(f"   Split line: {result.split_line}")
        print(f"   Node type: {result.candidate.node_type}")
        print(f"   Score: {result.candidate.score:.4f}")
        print(f"   Description: {result.candidate.description}")
        print(f"   Prefix length: {len(result.prefix)} chars")
        print(f"   Suffix length: {len(result.suffix)} chars")
        
        # 显示分割结果预览
        print("\nPrefix preview (first 200 chars):")
        print(result.prefix[:200] + "..." if len(result.prefix) > 200 else result.prefix)
        
        print("\nSuffix preview (first 200 chars):")
        print(result.suffix[:200] + "..." if len(result.suffix) > 200 else result.suffix)
        
        return True
    else:
        print("Split failed")
        return False

if __name__ == "__main__":
    main()
