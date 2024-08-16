import os
import aiohttp
from nonebot import on_message, get_bot
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, MessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException

waiting_for_url = {}

@event_preprocessor
async def preprocess_emoji_extract(bot: Bot, event: Event):
    if not isinstance(event, MessageEvent):
        return

    user_id = event.user_id
    msg = event.get_message().extract_plain_text().strip()

    if msg == "表情包提取":
        waiting_for_url[user_id] = True
        await bot.send(event, "已开启表情包提取功能，请发送表情包。发送 '取消' 以关闭此功能。")
        raise IgnoredException("表情包提取命令已处理")
    
    if user_id in waiting_for_url and waiting_for_url[user_id]:
        if msg == "取消":
            waiting_for_url[user_id] = False
            await bot.send(event, "表情包提取功能已关闭呜。")
            raise IgnoredException("表情包提取已取消")

        for seg in event.message:
            if seg.type == "mface":
                url = seg.data.get("url", "")
                if url:
                    await bot.send(event, f"提取到表情包完整链接了喵！( ´ ▽ ` ) ：\n{url}")
                    waiting_for_url[user_id] = False
                    raise IgnoredException("表情包已提取")
            elif seg.type == "image":
                url = seg.data.get("url", "")
                if url:
                    await bot.send(event, f"提取到图片链接了喵！( ´ ▽ ` ) ：\n{url}")
                    waiting_for_url[user_id] = False
                    raise IgnoredException("图片已提取")

        await bot.send(event, "抱歉，未能提取到表情包或图片链接呜。")
        waiting_for_url[user_id] = False
        raise IgnoredException("表情包提取失败")

    if user_id in waiting_for_url and waiting_for_url[user_id]:
        raise IgnoredException("等待用户发送表情包")