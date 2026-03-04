# test_deepseek.py
import os
from dotenv import load_dotenv
import inspect

load_dotenv()

try:
    import deepseek
    print(f"DeepSeek SDK版本: {deepseek.__version__ if hasattr(deepseek, '__version__') else '未知'}")
    
    from deepseek import DeepSeekClient
    
    # 查看DeepSeekClient有哪些方法
    print("\n=== DeepSeekClient 可用方法 ===")
    methods = [method for method in dir(DeepSeekClient) if not method.startswith('_')]
    for method in methods:
        print(f"- {method}")
    
    # 尝试查看chat_completion方法的签名
    if hasattr(DeepSeekClient, 'chat_completion'):
        print("\n=== chat_completion 方法参数 ===")
        signature = inspect.signature(DeepSeekClient.chat_completion)
        print(f"参数: {signature}")
    
    # 尝试创建一个简单的客户端并查看可用方法
    client = DeepSeekClient(api_key=os.getenv("DEEPSEEK_API_KEY"))
    print("\n=== 实例方法 ===")
    instance_methods = [method for method in dir(client) if not method.startswith('_')]
    for method in instance_methods:
        print(f"- {method}")
        
except ImportError as e:
    print(f"导入错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")