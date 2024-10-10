from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException

@event_preprocessor
async def preprocess_set_special_title(bot: Bot, event: Event):
    if isinstance(event, GroupMessageEvent):
        message = event.get_plaintext()
        if message.startswith("给我头衔 "):
            try:
                await handle_set_special_title(bot, event)
            except Exception as e:
                await bot.send(event, f"设置头衔时出错：{str(e)}")
            finally:
                raise IgnoredException("头衔设置命令已处理")

async def handle_set_special_title(bot: Bot, event: GroupMessageEvent):
    message = event.get_plaintext()
    special_title = message[5:]
    user_id = event.user_id
    await bot.call_api("set_group_special_title", group_id=event.group_id, user_id=user_id, special_title=special_title)
    return
