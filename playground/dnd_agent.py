# dnd_game_fixed.py
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 检查API密钥
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("❌ 错误: 没有找到DEEPSEEK_API_KEY环境变量")
    print("请在.env文件中添加: DEEPSEEK_API_KEY=your-api-key-here")
    sys.exit(1)

try:
    from deepseek import DeepSeekClient
except ImportError:
    print("❌ 错误: 未安装deepseek-sdk")
    print("请运行: pip install deepseek-sdk")
    sys.exit(1)

class DNDGameMaster:
    def __init__(self):
        print("🤖 初始化D&D游戏大师...")
        self.client = DeepSeekClient(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        )
        self.game_state = {
            "player_hp": 12,
            "location": "矿井入口",
            "inventory": ["长剑", "火把", "3个金币"],
            "history": []
        }
        
    def get_adventure_start(self):
        """获取冒险开场白"""
        messages = [
            {"role": "system", "content": "你是一个D&D地下城主，擅长创建精彩的微型冒险。"},
            {"role": "user", "content": """请为一位1级战士玩家生成一个3-5分钟的微型冒险开场。
场景设定在废弃矿井，有哥布林敌人。
请用生动的描述开场，并在最后给出三个行动选项（A、B、C）。"""}
        ]
        
        try:
            response = self.client.chat_completion(
                messages=messages,  # 注意这里是messages参数，不是prompt
                model="deepseek-chat",
                temperature=0.8,
                max_tokens=500
            )
            # 根据实际返回格式调整
            if isinstance(response, dict):
                return response.get('choices', [{}])[0].get('message', {}).get('content', str(response))
            return str(response)
        except Exception as e:
            print(f"API错误详情: {e}")
            return f"""❌ API调用失败，使用备用开场：

你站在昏暗的矿井入口，火把的光芒照出潮湿的矿道。空气中弥漫着霉味和...血腥味？
前方传来可疑的嘎嘎声和金属碰撞声。

你要：
A. 悄悄前进，熄灭火光
B. 点燃火把大声警告"谁在里面？"
C. 扔个石头探路，然后躲在阴影中观察"""
    
    def process_action(self, action):
        """处理玩家行动"""
        # 构建对话历史
        messages = [
            {"role": "system", "content": f"""你是一个D&D地下城主。当前游戏状态：
- 玩家HP: {self.game_state['player_hp']}/12
- 位置: {self.game_state['location']}
- 背包: {', '.join(self.game_state['inventory'])}
- 历史行动: {', '.join(self.game_state['history'][-3:]) if self.game_state['history'] else '刚刚开始冒险'}"""}
        ]
        
        # 添加历史对话（简化版）
        for hist in self.game_state['history'][-2:]:
            messages.append({"role": "user", "content": hist})
            messages.append({"role": "assistant", "content": "（之前已回应）"})
        
        # 添加当前行动
        messages.append({"role": "user", "content": f"我选择：{action}。请描述这个行动的结果并推进剧情，最后给出2-3个新的行动选项。"})
        
        try:
            response = self.client.chat_completion(
                messages=messages,
                model="deepseek-chat",
                temperature=0.8,
                max_tokens=600
            )
            
            # 更新游戏状态（简化版）
            self.game_state['history'].append(action)
            if len(self.game_state['history']) > 5:
                self.game_state['history'].pop(0)
            
            # 根据返回格式提取内容
            if isinstance(response, dict):
                return response.get('choices', [{}])[0].get('message', {}).get('content', str(response))
            return str(response)
            
        except Exception as e:
            print(f"API错误详情: {e}")
            return f"""❌ API调用失败，但剧情继续...

你的行动"{action}"产生了效果！前方传来哥布林的尖叫声和混乱的脚步声。

接下来你要：
1. 继续前进，准备战斗
2. 后退寻找掩护
3. 大声喊话试图沟通"""
    
    def play(self):
        """主游戏循环"""
        print("\n" + "="*50)
        print("      🐉 D&D 微型冒险：矿井突袭 🗡️")
        print("="*50)
        
        # 获取开场白
        print("\n📖 开场白:")
        print("-"*30)
        opening = self.get_adventure_start()
        print(opening)
        
        # 游戏主循环
        turns = 0
        max_turns = 5
        
        while turns < max_turns:
            print("\n" + "-"*30)
            action = input("⚔️ 你的行动 (输入A/B/C或文字描述，输入quit退出): ").strip()
            
            if action.lower() in ['quit', 'exit', 'q']:
                print("👋 感谢游玩！")
                break
            
            if not action:
                print("请输入行动")
                continue
            
            print("\n🤖 DM回应:")
            print("-"*30)
            response = self.process_action(action)
            print(response)
            
            turns += 1
            
            # 简单检查是否到达结局
            if any(word in response for word in ["冒险结束", "胜利", "失败", "逃出", "完成任务"]):
                print("\n🏁 冒险自然结束！")
                break
        
        if turns >= max_turns:
            print("\n⏰ 5回合已到，冒险暂告一段落！")
        
        print("\n" + "="*50)
        print("📊 游戏统计")
        print(f"- 总回合数: {turns}")
        print(f"- 最终HP: {self.game_state['player_hp']}/12")
        print(f"- 探索地点: {self.game_state['location']}")
        print("="*50)

# 测试模式（不需要API）
def test_mode():
    """测试模式 - 不需要API"""
    print("\n" + "="*50)
    print("      🎲 D&D 微型冒险 (测试模式) 🎲")
    print("="*50)
    print("\n📖 你站在矿井入口，火把的光芒照出潮湿的矿道...")
    print("\n前方传来哥布林的叫声！你要：")
    print("A. 悄悄潜行过去")
    print("B. 直接冲进去战斗")
    print("C. 设置陷阱引诱它们")
    
    turns = 0
    hp = 12
    location = "矿井入口"
    
    story_segments = []
    
    while turns < 3:
        print("\n" + "-"*30)
        action = input("⚔️ 你的选择 (A/B/C 或输入quit退出): ").strip().upper()
        
        if action in ['QUIT', 'Q']:
            break
        
        if turns == 0:
            if action == 'A':
                story = "你悄悄潜行，发现3只哥布林正在分赃。它们背对着你，毫无防备。"
                options = "\n接下来：\n1. 偷袭它们\n2. 偷走它们的财物\n3. 等待更多信息"
            elif action == 'B':
                story = "你冲了进去！哥布林惊慌失措，战斗开始！你一剑砍倒一只，但被另一只划伤了手臂 (HP-2)。剩下的哥布林在逃跑！"
                hp -= 2
                options = "\n接下来：\n1. 追击逃跑的哥布林\n2. 检查被砍倒的哥布林\n3. 谨慎前进"
            elif action == 'C':
                story = "你设置了一个精妙的陷阱，一只哥布林踩中被吊了起来！它的同伴们尖叫着逃向洞穴深处。"
                options = "\n接下来：\n1. 审问被吊起的哥布林\n2. 沿着逃跑路线追踪\n3. 先搜刮陷阱周围"
            else:
                story = "你犹豫了一下，但冒险必须继续..."
                options = "\n接下来：\n1. 继续前进\n2. 退回入口\n3. 大声喊话"
            
            story_segments.append(story)
            print(f"\n🤖 {story}{options}")
            location = "矿井通道"
            
        elif turns == 1:
            if action in ['1', 'A']:
                story = "你果断行动！哥布林措手不及，战斗很快结束。你在尸体上找到了一把生锈的短剑和5个铜币。"
                options = "\n前方出现岔路：\n1. 向左走（有水声）\n2. 向右走（有臭味）\n3. 仔细检查地面痕迹"
            elif action in ['2', 'B']:
                story = "你找到了一个隐藏的矿工营地，里面有废弃的工具和半瓶烈酒。"
                options = "\n远处传来脚步声：\n1. 躲起来观察\n2. 主动迎上去\n3. 从另一边绕开"
            else:
                story = "你继续探索，发现了一个巨大的洞穴。"
                options = "\n洞穴中有：\n1. 发光的蘑菇\n2. 沉睡的巨魔\n3. 古老的矿车"
            
            story_segments.append(story)
            print(f"\n🤖 {story}{options}")
            
        elif turns == 2:
            story = "你做出了最终选择！眼前出现了出口的光芒，你成功完成了这次矿井探险！"
            story_segments.append(story)
            print(f"\n🤖 {story}")
            print("\n✨ 冒险成功！你获得了20点经验值！")
            break
        
        turns += 1
    
    # 生成故事总结
    print("\n" + "="*50)
    print("📖 你的冒险故事")
    print("="*50)
    for i, segment in enumerate(story_segments, 1):
        print(f"\n第{i}章:\n{segment}")
    
    print("\n" + "="*50)
    print(f"🏁 冒险结束 | 最终HP: {hp}/12 | 探索区域: {location}")
    print("="*50)

# 简化版测试，直接检查API格式
def test_api_format():
    """测试API格式"""
    try:
        from deepseek import DeepSeekClient
        client = DeepSeekClient(api_key=api_key)
        
        # 测试最简单的调用
        messages = [
            {"role": "user", "content": "Say hello"}
        ]
        
        print("正在测试API连接...")
        response = client.chat_completion(messages=messages)
        print(f"API响应: {response}")
        print("✅ API连接成功！")
        return True
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        print("\n可能的原因:")
        print("1. API密钥不正确")
        print("2. 网络连接问题")
        print("3. SDK版本不兼容")
        return False

if __name__ == "__main__":
    print("选择模式:")
    print("1. 真实模式 (需要API密钥)")
    print("2. 测试模式 (无需API，内置简单剧情)")
    print("3. 测试API格式 (检查连接)")
    
    choice = input("请输入1、2或3: ").strip()
    
    if choice == "1":
        if not os.path.exists(".env"):
            print("⚠️  未找到.env文件，正在创建模板...")
            with open(".env", "w") as f:
                f.write("# DeepSeek API配置\n")
                f.write("DEEPSEEK_API_KEY=你的API密钥在这里\n")
                f.write("DEEPSEEK_BASE_URL=https://api.deepseek.com/v1\n")
            print("✅ 已创建.env文件，请编辑填入你的API密钥")
            print("然后重新运行程序")
        else:
            # 先测试API
            if test_api_format():
                game = DNDGameMaster()
                game.play()
            else:
                print("\n是否进入测试模式？(y/n)")
                if input().lower() == 'y':
                    test_mode()
    elif choice == "2":
        test_mode()
    elif choice == "3":
        test_api_format()
    else:
        print("无效选择")