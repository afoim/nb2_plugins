import os
import random
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.params import CommandArg
from nonebot.log import logger

# 使用 on_command 装饰器来定义命令
geiwocao = on_command("给我草", priority=5)

@geiwocao.handle()
async def handle_geiwocao(bot: Bot, event: Event, args: Message = CommandArg()):
    # 检查是否@了Bot
    if not event.is_tome():
        return

    # 定义文件路径
    file_path = os.path.join(os.path.dirname(__file__), 'geiwocaolist', 'geiwocao.txt')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取所有行
            lines = f.readlines()
            
            if lines:
                # 随机选择一行
                chosen_line = random.choice(lines).strip()
                # 发送消息
                await geiwocao.finish(MessageSegment.text(chosen_line))
            else:
                await geiwocao.finish("文件内容为空。")
    except Exception as e:
        logger.error(f"读取文件时发生错误: {e}")
        return