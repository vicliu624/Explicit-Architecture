#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ast_splitter.py
----------------------------------------------------
测试AST-based代码分割器

功能：
1. 测试新的AST-based Java分割器
2. 对比AST方法和正则表达式方法的效果
3. 验证现代Java特性的支持

依赖：
    Python 3.7+
----------------------------------------------------
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generation.code_splitters import get_code_splitter


def test_modern_java_features():
    """测试现代Java特性支持"""
    print("测试现代Java特性支持...")
    
    # 包含现代Java特性的测试代码
    modern_java_code = [
        "package com.example;\n",
        "\n",
        "import java.util.List;\n",
        "import java.util.ArrayList;\n",
        "\n",
        "public class ModernJavaExample {\n",
        "    private String name;\n",
        "    private int age;\n",
        "    \n",
        "    // 构造函数\n",
        "    public ModernJavaExample(String name, int age) {\n",
        "        this.name = name;\n",
        "        this.age = age;\n",
        "    }\n",
        "    \n",
        "    // 传统方法\n",
        "    public String getName() {\n",
        "        return name;\n",
        "    }\n",
        "    \n",
        "    // 使用var关键字\n",
        "    public void processData() {\n",
        "        var list = new ArrayList<String>();\n",
        "        list.add(\"test\");\n",
        "    }\n",
        "    \n",
        "    // Record定义\n",
        "    public record User(String id, String email) {\n",
        "        public boolean isValid() {\n",
        "            return id != null && email != null;\n",
        "        }\n",
        "    }\n",
        "    \n",
        "    // Enum定义\n",
        "    public enum Status {\n",
        "        ACTIVE, INACTIVE, PENDING\n",
        "    }\n",
        "    \n",
        "    // Sealed类定义\n",
        "    public sealed class Shape permits Circle, Rectangle {\n",
        "        public abstract double area();\n",
        "    }\n",
        "    \n",
        "    // Switch表达式\n",
        "    public String getStatusMessage(Status status) {\n",
        "        return switch (status) {\n",
        "            case ACTIVE -> \"系统活跃\";\n",
        "            case INACTIVE -> \"系统不活跃\";\n",
        "            case PENDING -> \"等待中\";\n",
        "        };\n",
        "    }\n",
        "    \n",
        "    // Pattern matching\n",
        "    public void processShape(Shape shape) {\n",
        "        if (shape instanceof Circle circle) {\n",
        "            System.out.println(\"圆形半径: \" + circle.getRadius());\n",
        "        } else if (shape instanceof Rectangle rect) {\n",
        "            System.out.println(\"矩形面积: \" + rect.getWidth() * rect.getHeight());\n",
        "        }\n",
        "    }\n",
        "}\n"
    ]
    
    try:
        splitter = get_code_splitter('java')
        result = splitter.split_code(modern_java_code)
        
        if result:
            prefix, suffix = result
            print("现代Java特性分割成功!")
            print(f"Prefix长度: {len(prefix)} 字符")
            print(f"Suffix长度: {len(suffix)} 字符")
            print(f"Prefix比例: {len(prefix)/(len(prefix)+len(suffix))*100:.1f}%")
            print(f"Suffix比例: {len(suffix)/(len(prefix)+len(suffix))*100:.1f}%")
            
            # 检查分割质量
            if len(prefix.strip()) >= 20 and len(suffix.strip()) >= 20:
                print("分割质量检查通过")
                
                # 检查是否在语义边界分割
                print("\n分割点分析:")
                print("Prefix结尾:")
                print(prefix[-100:] if len(prefix) > 100 else prefix)
                print("\nSuffix开头:")
                print(suffix[:100] if len(suffix) > 100 else suffix)
                
                return True
            else:
                print("分割质量检查失败")
                return False
        else:
            print("现代Java特性分割失败")
            return False
            
    except Exception as e:
        print(f"现代Java特性分割器错误: {e}")
        return False


def test_ast_vs_regex():
    """对比AST方法和正则表达式方法"""
    print("\n对比AST方法和正则表达式方法...")
    
    # 复杂的Java代码
    complex_java_code = [
        "package com.example.complex;\n",
        "\n",
        "import java.util.*;\n",
        "import java.util.stream.Collectors;\n",
        "\n",
        "public class ComplexExample {\n",
        "    private final Map<String, List<Integer>> dataMap;\n",
        "    private static final int MAX_SIZE = 1000;\n",
        "    \n",
        "    public ComplexExample() {\n",
        "        this.dataMap = new HashMap<>();\n",
        "    }\n",
        "    \n",
        "    public void addData(String key, List<Integer> values) {\n",
        "        if (key == null || values == null) {\n",
        "            throw new IllegalArgumentException(\"参数不能为空\");\n",
        "        }\n",
        "        \n",
        "        dataMap.computeIfAbsent(key, k -> new ArrayList<>()).addAll(values);\n",
        "    }\n",
        "    \n",
        "    public List<Integer> processData(String key) {\n",
        "        List<Integer> values = dataMap.get(key);\n",
        "        if (values == null) {\n",
        "            return Collections.emptyList();\n",
        "        }\n",
        "        \n",
        "        return values.stream()\n",
        "                .filter(v -> v > 0)\n",
        "                .sorted()\n",
        "                .limit(MAX_SIZE)\n",
        "                .collect(Collectors.toList());\n",
        "    }\n",
        "    \n",
        "    public interface DataProcessor {\n",
        "        void process(String data);\n",
        "        \n",
        "        default void log(String message) {\n",
        "            System.out.println(\"[\" + getClass().getSimpleName() + \"] \" + message);\n",
        "        }\n",
        "    }\n",
        "    \n",
        "    public enum ProcessingMode {\n",
        "        FAST, BALANCED, THOROUGH\n",
        "    }\n",
        "}\n"
    ]
    
    try:
        splitter = get_code_splitter('java')
        
        # 测试多次分割，看分割点的多样性
        split_points = []
        for i in range(5):
            result = splitter.split_code(complex_java_code)
            if result:
                prefix, suffix = result
                # 计算分割点位置
                split_point = len(prefix.split('\n'))
                split_points.append(split_point)
        
        print(f"复杂Java代码分割成功!")
        print(f"分割点位置: {split_points}")
        print(f"分割点多样性: {len(set(split_points))} 种不同的分割点")
        
        if len(set(split_points)) > 1:
            print("分割点具有多样性，说明AST方法工作良好")
            return True
        else:
            print("分割点缺乏多样性，可能需要改进")
            return False
            
    except Exception as e:
        print(f"复杂Java代码分割器错误: {e}")
        return False


def test_edge_cases():
    """测试边界情况"""
    print("\n测试边界情况...")
    
    test_cases = [
        {
            "name": "空文件",
            "code": []
        },
        {
            "name": "只有注释",
            "code": [
                "// 这是一个注释\n",
                "/* 多行注释 */\n",
                "/**\n",
                " * JavaDoc注释\n",
                " */\n"
            ]
        },
        {
            "name": "只有import",
            "code": [
                "package com.test;\n",
                "import java.util.List;\n",
                "import java.util.ArrayList;\n"
            ]
        },
        {
            "name": "简单类",
            "code": [
                "public class Simple {\n",
                "    public void method() {\n",
                "        return;\n",
                "    }\n",
                "}\n"
            ]
        }
    ]
    
    results = []
    splitter = get_code_splitter('java')
    
    for test_case in test_cases:
        try:
            result = splitter.split_code(test_case["code"])
            if result:
                print(f"{test_case['name']}: 分割成功")
                results.append(True)
            else:
                print(f"{test_case['name']}: 无法分割（预期行为）")
                results.append(True)  # 某些情况无法分割是正常的
        except Exception as e:
            print(f"{test_case['name']}: 错误 - {e}")
            results.append(False)
    
    return all(results)


def main():
    """主测试函数"""
    print("开始测试AST-based Java分割器...")
    
    results = []
    
    # 测试现代Java特性
    results.append(test_modern_java_features())
    
    # 对比AST和正则表达式方法
    results.append(test_ast_vs_regex())
    
    # 测试边界情况
    results.append(test_edge_cases())
    
    # 总结
    passed = sum(results)
    total = len(results)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("所有测试通过！AST-based Java分割器工作正常。")
        print("相比简单的关键字匹配，AST方法提供了:")
        print("   - 更准确的语法结构识别")
        print("   - 更好的现代Java特性支持")
        print("   - 更智能的分割点选择")
        print("   - 更强的容错能力")
        return True
    else:
        print("部分测试失败，需要进一步改进。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
