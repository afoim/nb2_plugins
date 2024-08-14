import os
import re
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.params import CommandArg

# 定义命令处理器
cmd_command = on_command('/cmd')
help_command = on_command('/help')

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
    # 获取第一个###之前的内容
    first_section = content.split('###', 1)[0].strip()
    original_message_id = event.message_id
    reply_message = MessageSegment.reply(original_message_id) + first_section
    await cmd_command.finish(reply_message)

@help_command.handle()
async def handle_help_command(bot: Bot, event: Event, args: Message = CommandArg()):
    command = args.extract_plain_text().strip()
    
    if not command:
        await help_command.finish("请指定要查看帮助的命令，例如：/help openport")
    
    content = get_help_content(command)
    original_message_id = event.message_id
    reply_message = MessageSegment.reply(original_message_id) + content
    await help_command.finish(reply_message)
