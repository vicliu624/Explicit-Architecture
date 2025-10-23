#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_real_projects.py
测试真实项目目录
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.direct_data_builder import make_completion_samples

def test_project(project_path, project_name):
    """测试单个项目"""
    print(f"测试项目: {project_name}")
    print(f"路径: {project_path}")
    print(f"目录存在: {os.path.exists(project_path)}")
    
    if not os.path.exists(project_path):
        print("项目目录不存在，跳过")
        return None
    
    print("开始处理项目...")
    try:
        samples = make_completion_samples(project_path, 'explicit')
        print(f"生成了 {len(samples)} 个样本")
        
        # 显示前几个样本的信息
        for i, sample in enumerate(samples[:3]):
            print(f"样本 {i+1}:")
            print(f"  文件: {sample['file']}")
            print(f"  语言: {sample['language']}")
            if 'split_score' in sample:
                print(f"  分割评分: {sample['split_score']:.4f}")
                print(f"  分割类型: {sample['split_type']}")
                print(f"  分割描述: {sample['split_description']}")
            print(f"  前缀长度: {len(sample['prefix'])} 字符")
            print(f"  后缀长度: {len(sample['suffix'])} 字符")
            print()
        
        return samples
    except Exception as e:
        print(f"处理项目失败: {e}")
        return None

def main():
    """主测试函数"""
    print("=" * 80)
    print("测试真实项目目录")
    print("=" * 80)
    
    # 测试项目1
    project1_path = r"C:\Users\vicliu\IdeaProjects\ynyt-cloud\ynyt-cloud-fund-service\src\main"
    samples1 = test_project(project1_path, "ynyt-cloud-fund-service")
    
    print("\n" + "-" * 80 + "\n")
    
    # 测试项目2
    project2_path = r"C:\Users\vicliu\Downloads\explict"
    samples2 = test_project(project2_path, "explict")
    
    print("\n" + "=" * 80)
    print("测试总结:")
    print(f"项目1样本数: {len(samples1) if samples1 else 0}")
    print(f"项目2样本数: {len(samples2) if samples2 else 0}")
    print("=" * 80)

if __name__ == "__main__":
    main()
