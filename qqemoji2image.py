import os
import aiohttp
from nonebot import on_command
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, MessageEvent

extract_emoji = on_command("表情包提取", priority=5)

@extract_emoji.handle()
async def handle_first_receive(bot: Bot, event: Event, state: T_State):
    await extract_emoji.send("已开启表情包提取功能，请发送表情包。发送 '取消' 以关闭此功能。")

@extract_emoji.got("emoji")
async def handle_emoji(bot: Bot, event: MessageEvent, state: T_State):
    if event.get_message().extract_plain_text().strip() == "取消":
        await extract_emoji.finish("表情包提取功能已关闭呜。")

    for seg in event.get_message():
        if seg.type == "mface":
            url = seg.data.get("url", "")
            if url:
                await extract_emoji.finish(f"提取到表情包完整链接了喵！( ´ ▽ ` ) ：\n{url}")
        elif seg.type == "image":
            url = seg.data.get("url", "")
            if url:
                await extract_emoji.finish(f"提取到图片链接了喵！( ´ ▽ ` ) ：\n{url}")

    await extract_emoji.reject("抱歉，未能提取到表情包或图片链接呜。请再次发送表情包或发送 '取消' 以关闭功能。")