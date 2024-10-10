import re
import aiohttp
import logging
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定义命令触发器
bilimusic_cmd = on_command("/bilimusic", priority=5)

@bilimusic_cmd.handle()
async def handle_message(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    
    # 定义请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bilibili.com/"
    }
    
    # 正则表达式匹配BV号
    bv_pattern = re.compile(r'(BV[0-9A-Za-z]+)')
    match = bv_pattern.search(message)
    
    if match:
        bv_id = match.group(1)
    else:
        # 如果没有找到BV号，检查URL是否是b23.tv短链接
        short_link_pattern = re.compile(r'(https?://b23.tv/\w+)')
        short_link_match = short_link_pattern.search(message)
        
        if short_link_match:
            short_link = short_link_match.group(1)
            
            # 请求短链接进行重定向获取真实链接
            async with aiohttp.ClientSession() as session:
                async with session.get(short_link, headers=headers, allow_redirects=True) as response:
                    final_url = str(response.url)
                    
                    bv_match = bv_pattern.search(final_url)
                    if bv_match:
                        bv_id = bv_match.group(1)
                    else:
                        reply_message = "未能提取BV号，请提供有效的Bilibili视频链接。"
                        await bilimusic_cmd.finish(reply_message, at_sender=True)
                        return
        else:
            reply_message = "未能提取BV号，请提供有效的Bilibili视频链接。"
            await bilimusic_cmd.finish(reply_message, at_sender=True)
            return
    
    # 请求获取视频的 cid
    api_url_pagelist = f"https://api.bilibili.com/x/player/pagelist?bvid={bv_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url_pagelist, headers=headers) as response:
            data = await response.json()
            if data.get("code") == 0:
                cid_list = data.get("data", [])
                if cid_list:
                    cid = cid_list[0].get("cid")
                    if cid:
                        # 请求获取视频的 bgm_info
                        api_url_bgm = f"https://api.bilibili.com/x/player/wbi/v2?bvid={bv_id}&cid={cid}"
                        
                        async with session.get(api_url_bgm, headers=headers) as response:
                            data = await response.json()
                            if data.get("code") == 0:
                                bgm_info = data.get("data", {}).get("bgm_info")
                                if bgm_info:
                                    jump_url = bgm_info.get("jump_url")
                                    if jump_url:
                                        reply_message = f"音乐跳转链接: {jump_url}"
                                    else:
                                        reply_message = "错误：未找到 BGM 跳转链接。"
                                else:
                                    reply_message = "错误：未找到 BGM 信息。"
                            else:
                                reply_message = f"请求失败: {data.get('message')}"
                    else:
                        reply_message = "错误：未找到视频 CID。"
                else:
                    reply_message = "错误：未找到视频信息。"
            else:
                reply_message = f"请求失败: {data.get('message')}"
    
    # 引用原始消息并发送回复
    original_message_id = event.message_id
    reply_segment = MessageSegment.reply(original_message_id)
    await bilimusic_cmd.finish(reply_segment + reply_message, at_sender=True)