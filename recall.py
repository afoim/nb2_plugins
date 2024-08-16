from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State

__plugin_meta__ = PluginMetadata(
    name="消息撤回",
    description="撤回机器人发送的消息",
    usage="/recall [引用消息]",
)

recall = on_command("recall", priority=5, block=True)

@recall.handle()
async def handle_recall(bot: Bot, event: GroupMessageEvent, state: T_State):
    # 检查是否有引用消息
    reply = event.reply
    if reply:
        # 如果有引用消息, 尝试撤回引用的消息
        message_id = reply.message_id
    else:
        # 如果没有引用消息, 无法撤回
        await recall.finish("请引用要撤回的消息")
    
    try:
        # 尝试撤回机器人发送的消息
        await bot.delete_msg(message_id=message_id)
        # 成功撤回后，尝试撤回发起人的 /recall 消息
        await bot.delete_msg(message_id=event.message_id)
    except Exception as e:
        await recall.finish(f"撤回失败：{str(e)}")