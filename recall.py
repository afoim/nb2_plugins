from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State

__plugin_meta__ = PluginMetadata(
    name="消息撤回",
    description="撤回机器人发送的消息",
    usage="/recall [引用消息]",
)

last_message = {}

recall = on_command("recall", priority=5, block=True)

@recall.handle()
async def handle_recall(bot: Bot, event: GroupMessageEvent, state: T_State):
    # 检查是否有引用消息
    reply = event.reply
    if reply:
        # 如果有引用消息,尝试撤回引用的消息
        message_id = reply.message_id
    else:
        # 如果没有引用消息,尝试撤回最后一条消息
        group_id = event.group_id
        if group_id not in last_message:
            await recall.finish("没有可以撤回的消息")
        message_id = last_message[group_id]
    
    try:
        await bot.delete_msg(message_id=message_id)
    except Exception as e:
        return

# 记录机器人发送的最后一条消息
record_last_message = on_message(priority=5, block=False)

@record_last_message.handle()
async def handle_record(bot: Bot, event: GroupMessageEvent):
    if event.user_id == bot.self_id:
        last_message[event.group_id] = event.message_id