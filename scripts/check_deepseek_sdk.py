#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek 客户端测试文件
用 uv run python test_deepseek.py 执行
"""

import sys
print(f"当前 Python 路径: {sys.executable}")
print(f"Python 版本: {sys.version}")

try:
    # 方法1：尝试导入 deepseek 包
    import deepseek
    print(f"\n✅ deepseek 包已找到")
    print(f"包路径: {deepseek.__file__}")
    
    # 查看包中所有可用的属性和方法
    print("\n📦 deepseek 包内容:")
    for item in dir(deepseek):
        if not item.startswith('_'):  # 不显示私有属性
            print(f"  - {item}")
    
    # 方法2：尝试各种可能的导入方式
    print("\n🔍 尝试不同的导入方式:")
    
    # 尝试导入 DeepSeekClient
    try:
        from deepseek import DeepSeekClient
        print("  ✅ from deepseek import DeepSeekClient 成功")
        # 如果能导入，尝试创建实例（不需要真实 API key）
        client = DeepSeekClient(api_key="test")
        print("  ✅ 可以创建 DeepSeekClient 实例")
    except ImportError as e:
        print(f"  ❌ from deepseek import DeepSeekClient 失败: {e}")
    
    # 尝试导入 DeepSeekAPI
    try:
        from deepseek import DeepSeekAPI
        print("  ✅ from deepseek import DeepSeekAPI 成功")
    except ImportError:
        print("  ❌ from deepseek import DeepSeekAPI 失败")
    
    # 尝试导入 Client
    try:
        from deepseek import Client
        print("  ✅ from deepseek import Client 成功")
    except ImportError:
        print("  ❌ from deepseek import Client 失败")
    
    # 尝试导入 api 模块
    try:
        from deepseek import api
        print("  ✅ from deepseek import api 成功")
        if hasattr(api, 'Client'):
            print("  ✅ api 模块中有 Client 类")
    except ImportError:
        print("  ❌ from deepseek import api 失败")
    
    # 查看是否有版本信息
    if hasattr(deepseek, '__version__'):
        print(f"\n📌 deepseek 版本: {deepseek.__version__}")
    
except ImportError as e:
    print(f"❌ 导入 deepseek 失败: {e}")
    print("\n请确认包已安装: uv pip install deepseek")
    
except Exception as e:
    print(f"❌ 其他错误: {e}")

print("\n✨ 测试完成")