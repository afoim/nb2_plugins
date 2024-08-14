import base64
import re
import aiohttp
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import MessageSegment

# 定义命令触发器
image_reply = on_command("/bilicover", priority=5)

@image_reply.handle()
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
            # 请求短链接进行重定向获取真实链接
            async with aiohttp.ClientSession() as session:
                async with session.get(short_link_match.group(1), headers=headers) as response:
                    final_url = str(response.url)
                    bv_match = bv_pattern.search(final_url)
                    if bv_match:
                        bv_id = bv_match.group(1)
                    else:
                        await image_reply.send("未能提取BV号，请提供有效的Bilibili视频链接。")
                        return
        else:
            await image_reply.send("未能提取BV号，请提供有效的Bilibili视频链接。")
            return
    
    # 构建API请求URL
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
    
    # 请求API获取视频信息
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            data = await response.json()
            if data.get("code") == 0:
                pic_url = data.get("data", {}).get("pic")
                if pic_url:
                    async with session.get(pic_url, headers=headers) as pic_response:
                        img_data = await pic_response.read()
                        img_base64 = base64.b64encode(img_data).decode("utf-8")
                        img_segment = MessageSegment.image(f"base64://{img_base64}")
                        original_message_id = event.message_id
                        reply_message = MessageSegment.reply(original_message_id) + (img_segment)
                        await image_reply.send(reply_message)
                else:
                    await image_reply.send("未找到封面图片。")
            else:
                await image_reply.send(f"请求失败: {data.get('message')}")
