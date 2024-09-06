import os
import re
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, Message, GroupMessageEvent, PrivateMessageEvent

# 定义命令处理器
cmd_command = on_command('/cmd')

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
cmd_file_path = os.path.join(current_dir, 'cmdlist', 'cmd.txt')

def read_cmd_file():
    if os.path.exists(cmd_file_path):
        with open(cmd_file_path, 'r', encoding='utf-8') as file:
            return file.read()
    return "命令列表不可用"

def get_help_content(command):
    content = read_cmd_file()
    pattern = rf"###\s*{re.escape(command)}(.*?)(?=###|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return f"插件 {command} 的详情不可用"

@cmd_command.handle()
async def handle_cmd_command(bot: Bot, event: Event):
    content = read_cmd_file()
    
    # 分割内容,获取开头部分和命令列表部分
    parts = content.split('###', 1)
    header = parts[0].strip()
    sections = re.split(r'###', parts[1]) if len(parts) > 1 else []

    msg_list = [
        {
            "type": "node",
            "data": {
                "name": "命令列表说明",
                "uin": str(event.self_id),
                "content": header
            }
        }
    ]
    
    for i, section in enumerate(sections, start=1):
        lines = section.strip().split('\n')
        if lines:
            command = lines[0].strip()
            description = '\n'.join(lines[1:]).strip()
            msg_list.append({
                "type": "node",
                "data": {
                    "name": f"命令 {i}",
                    "uin": str(event.self_id),
                    "content": f"{command}\n{description}"
                }
            })

    try:
        if isinstance(event, GroupMessageEvent):  # 如果是群聊
            await bot.call_api(
                "send_group_forward_msg",
                group_id=event.group_id,
                messages=msg_list
            )
        elif isinstance(event, PrivateMessageEvent):  # 如果是私聊
            await bot.call_api(
                "send_private_forward_msg",
                user_id=event.user_id,
                messages=msg_list
            )
    except Exception as e:
        await cmd_command.finish(f"发送命令列表失败：{str(e)}")
