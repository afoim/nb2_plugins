import subprocess
from datetime import datetime
from nonebot import on_command, Bot
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
import nonebot

# 创建命令处理器
info_command = on_command("/status", priority=5)

# 记录Bot启动时间
bot_start_time = datetime.now()

@info_command.handle()
async def handle_info(bot: Bot, event: MessageEvent):
    # 获取Bot的信息
    bot_info = await bot.get_login_info()
    friend_list = await bot.get_friend_list()
    group_list = await bot.get_group_list()
    friend_count = len(friend_list)
    group_count = len(group_list)

    # 获取系统信息
    system_info = get_fastfetch_info()

    # 获取Bot适配器名称
    adapter_name = bot.adapter.get_name()

    # 拼接NoneBot2信息
    nonebot_info = f"NoneBot2版本: {nonebot.__version__}\n"

    # 添加Bot相关信息
    nonebot_info += f"Bot账号: QQ {bot_info['user_id']}\n"
    nonebot_info += f"好友: {friend_count}个\n"
    nonebot_info += f"群聊: {group_count}个\n"
    nonebot_info += f"Bot连接协议: {adapter_name}\n"  # 添加Bot连接协议

    # 生成最终文本信息
    text_content = nonebot_info + system_info

    # 确保 reply_message 有效
    reply_message = MessageSegment.text(text_content)
    if event.message_id:  # 确保有有效的消息 ID
        reply_message = MessageSegment.reply(event.message_id) + reply_message

    await bot.send(event, reply_message)


def get_fastfetch_info():
    try:
        # 调用 fastfetch 并获取输出
        output = subprocess.check_output("fastfetch -l none", shell=True).decode().strip()
        
        # 删除最后 5 行
        lines = output.splitlines()  # 将输出按行分割成列表
        trimmed_output = "\n".join(lines[:-5])  # 去掉最后 5 行后重新拼接

        return trimmed_output
    except Exception as e:
        return f"无法获取系统信息：{str(e)}"

