# dnd_deepseek.py
import os
import sys
from dotenv import load_dotenv
from typing import List, Dict, Optional
from pathlib import Path

# 找到 app 目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 app/.env
load_dotenv(BASE_DIR / ".env")

# 检查API密钥
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("❌ 错误: 没有找到DEEPSEEK_API_KEY环境变量")
    print("请在.env文件中添加: DEEPSEEK_API_KEY=your-api-key-here")
    sys.exit(1)

# 导入deepseek包（注意：不是deepseek-sdk）
try:
    import deepseek
    from deepseek import DeepSeekClient
    print(f"✅ 成功导入 deepseek 包")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保已安装: uv add deepseek")
    sys.exit(1)

# 获取版本信息（可选）
def get_package_version():
    """尝试获取deepseek包版本"""
    try:
        # 方法1: 从包属性获取
        if hasattr(deepseek, '__version__'):
            return deepseek.__version__
        
        # 方法2: 使用importlib.metadata
        import importlib.metadata
        return importlib.metadata.version('deepseek')
    except:
        return "未知 (但功能正常)"

print(f"📦 deepseek 包版本: {get_package_version()}")

class DNDGameMaster:
    def __init__(self):
        print("🤖 初始化D&D游戏大师...")
        
        # 创建客户端 - deepseek包的初始化方式可能不同
        try:
            # 方式1: 直接传api_key
            self.client = DeepSeekClient(api_key=api_key)
        except TypeError:
            try:
                # 方式2: 可能需要用init方法
                deepseek.init(api_key=api_key)
                self.client = deepseek
            except:
                # 方式3: 最简单的客户端
                self.client = DeepSeekClient()
                self.client.api_key = api_key
        
        self.game_state = {
            "player_hp": 12,
            "player_max_hp": 12,
            "location": "矿井入口",
            "inventory": ["长剑", "火把", "3个金币"],
            "history": []
        }
        
        # 测试API连接
        self.test_connection()
    
    def test_connection(self):
        """测试API连接"""
        try:
            messages = [{"role": "user", "content": "Hello"}]
            
            # 尝试不同的调用方式
            if hasattr(self.client, 'chat_completion'):
                response = self.client.chat_completion(messages=messages)
            elif hasattr(self.client, 'ChatCompletion'):
                response = self.client.ChatCompletion.create(messages=messages)
            elif hasattr(deepseek, 'ChatCompletion'):
                response = deepseek.ChatCompletion.create(messages=messages)
            else:
                # 使用openai兼容模式
                from openai import OpenAI
                openai_client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com/v1"
                )
                response = openai_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages
                )
                self.client = openai_client  # 替换为openai客户端
                self.use_openai = True
            
            print("✅ API连接成功！")
        except Exception as e:
            print(f"⚠️ API连接测试失败: {e}")
            print("将使用离线模式运行")
    
    def call_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """调用DeepSeek API"""
        try:
            # 判断使用哪种客户端
            if hasattr(self, 'use_openai') and self.use_openai:
                # OpenAI兼容模式
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.8,
                    max_tokens=600
                )
                return response.choices[0].message.content
            
            # deepseek包模式
            if hasattr(self.client, 'chat_completion'):
                # 方法1: chat_completion方法
                response = self.client.chat_completion(
                    messages=messages,
                    model="deepseek-chat",
                    temperature=0.8,
                    max_tokens=600
                )
            elif hasattr(self.client, 'ChatCompletion'):
                # 方法2: ChatCompletion.create方法
                response = self.client.ChatCompletion.create(
                    messages=messages,
                    model="deepseek-chat",
                    temperature=0.8,
                    max_tokens=600
                )
            else:
                # 方法3: 直接使用deepseek模块
                response = deepseek.ChatCompletion.create(
                    messages=messages,
                    model="deepseek-chat",
                    temperature=0.8,
                    max_tokens=600
                )
            
            # 处理响应
            if hasattr(response, 'choices'):
                return response.choices[0].message.content
            elif isinstance(response, dict) and 'choices' in response:
                return response['choices'][0]['message']['content']
            else:
                return str(response)
                
        except Exception as e:
            print(f"❌ API调用错误: {e}")
            return None
    
    def get_adventure_start(self):
        """获取冒险开场白"""
        messages = [
            {"role": "system", "content": "你是一个D&D地下城主，擅长创建精彩的微型冒险。用中文回应。"},
            {"role": "user", "content": """请为一位1级战士玩家生成一个3-5分钟的微型冒险开场。
场景设定在废弃矿井，有哥布林敌人。
请用生动的描述开场，并在最后给出三个行动选项（A、B、C）。"""}
        ]
        
        print("📖 正在生成冒险开场...")
        response = self.call_api(messages)
        
        if response:
            return response
        else:
            return """你站在昏暗的矿井入口，火把的光芒照出潮湿的矿道。空气中弥漫着霉味和...血腥味？
前方传来可疑的嘎嘎声和金属碰撞声。

你要：
A. 悄悄前进，熄灭火光
B. 点燃火把大声警告"谁在里面？"
C. 扔个石头探路，然后躲在阴影中观察"""
    
    def process_action(self, action: str):
        """处理玩家行动"""
        system_prompt = f"""你是一个D&D地下城主。当前游戏状态：
- 玩家HP: {self.game_state['player_hp']}/{self.game_state['player_max_hp']}
- 位置: {self.game_state['location']}
- 背包: {', '.join(self.game_state['inventory'])}
- 最近行动: {', '.join(self.game_state['history'][-3:]) if self.game_state['history'] else '刚刚开始冒险'}

请用中文回应，描述行动结果，推进剧情。最后给出2-3个新的行动选项。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"我选择：{action}"}
        ]
        
        response = self.call_api(messages)
        
        # 更新游戏状态
        self.game_state['history'].append(action)
        if len(self.game_state['history']) > 5:
            self.game_state['history'].pop(0)
        
        # 简单尝试从回应中更新HP
        if response and any(word in response for word in ["受伤", "击中", "流血", "HP-"]):
            self.game_state['player_hp'] = max(0, self.game_state['player_hp'] - 2)
        
        return response or f"你的行动'{action}'产生了效果，冒险继续..."
    
    def play(self):
        """主游戏循环"""
        print("\n" + "="*60)
        print("      🐉 D&D 微型冒险：矿井突袭 🗡️")
        print("="*60)
        
        opening = self.get_adventure_start()
        print(f"\n📖 开场白:\n{'-'*40}\n{opening}")
        
        turns = 0
        max_turns = 5
        
        while turns < max_turns:
            print("\n" + "-"*40)
            print(f"💚 HP: {self.game_state['player_hp']}/{self.game_state['player_max_hp']}")
            print(f"📍 位置: {self.game_state['location']}")
            print("-"*40)
            
            action = input("⚔️ 你的行动 (输入A/B/C或文字描述，输入quit退出): ").strip()
            
            if action.lower() in ['quit', 'exit', 'q']:
                print("👋 感谢游玩！")
                break
            
            if not action:
                continue
            
            print("\n🤖 DM回应:")
            response = self.process_action(action)
            print(f"{'-'*40}\n{response}")
            
            turns += 1
            
            if response and any(word in response for word in ["冒险结束", "胜利", "失败", "逃出"]):
                print("\n🏁 冒险结束！")
                break
        
        if turns >= max_turns:
            print("\n⏰ 5回合已到，冒险暂告一段落！")
        
        self.generate_story()
    
    def generate_story(self):
        """生成冒险故事"""
        if not self.game_state['history']:
            return
        
        messages = [
            {"role": "system", "content": "你是一个叙事作家，擅长将游戏过程改编成短篇故事。"},
            {"role": "user", "content": f"""请将以下D&D游戏过程改写成一篇生动的短篇故事：

玩家职业：战士
最终HP：{self.game_state['player_hp']}/{self.game_state['player_max_hp']}
探索地点：{self.game_state['location']}
玩家行动：{', '.join(self.game_state['history'])}

请用中文写一个300字左右的短篇故事。"""}
        ]
        
        print("\n" + "="*60)
        print("📖 生成你的冒险故事...")
        story = self.call_api(messages)
        
        if story:
            print("\n✨ 你的冒险故事 ✨")
            print("="*60)
            print(story)
        else:
            print("\n✨ 冒险简记 ✨")
            print("="*60)
            print(f"战士手持长剑，勇敢探索了{self.game_state['location']}。")
            print(f"面对挑战，她做出了{len(self.game_state['history'])}个关键决定。")
            print("虽然伤痕累累，但她最终带着荣耀归来！")

def test_mode():
    """测试模式"""
    print("\n" + "="*60)
    print("      🎲 D&D 测试模式 🎲")
    print("="*60)
    
    hp = 12
    story = []
    
    scenes = [
        "你站在矿井入口，前方传来哥布林的叫声！",
        "你遇到了3只正在分赃的哥布林！",
        "你发现了矿井出口！"
    ]
    
    for i, scene in enumerate(scenes):
        print(f"\n📖 第{i+1}幕:\n{scene}")
        if i < len(scenes) - 1:
            action = input("\n⚔️ 你的行动: ").strip()
            story.append(action)
            if i == 1 and action.lower() in ['a', '1', '战斗', '攻击']:
                hp -= 2
                print("💥 战斗中受伤了！")
    
    print("\n" + "="*60)
    print("✨ 你的冒险故事 ✨")
    print("="*60)
    print(f"战士深入矿井，经历了{len(story)}次抉择，")
    print(f"最终以{hp}点生命值凯旋而归！")

if __name__ == "__main__":
    print("选择模式:")
    print("1. 真实模式 (需要API密钥)")
    print("2. 测试模式 (无需API)")
    
    choice = input("请输入1或2: ").strip()
    
    if choice == "1":
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("DEEPSEEK_API_KEY=你的API密钥在这里\n")
            print("✅ 已创建.env文件，请填入API密钥后重试")
        else:
            game = DNDGameMaster()
            game.play()
    else:
        test_mode()