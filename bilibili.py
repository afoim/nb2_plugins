import os
import base64
import asyncio
import re
import aiohttp
import json
import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment

# 设置 locale 为中文
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

# 创建 Bilibili URL 处理插件
bilibili_matcher = on_message(priority=5)

@bilibili_matcher.handle()
async def handle_bilibili_url(bot: Bot, event: Event):
    message = event.get_message()
    url = str(message)

    # 打印完整的消息
    #nonebot.logger.info(f"接收到的消息: {url}")

    # 尝试解析 JSON 数据
    json_pattern = re.compile(r'\[CQ:json,data=(\{.*?\})\]')
    json_match = json_pattern.search(url)
    if json_match:
        json_data = json_match.group(1)
        # 处理转义字符
        json_data = json_data.replace('&#44;', ',').replace('&amp;', '&')

        # 打印处理后的 JSON 数据
        #nonebot.logger.info(f"处理后的 JSON 数据: {json_data}")

        try:
            data_dict = json.loads(json_data)
            qqdocurl = data_dict.get('meta', {}).get('detail_1', {}).get('qqdocurl')
            if qqdocurl:
                nonebot.logger.info(f"提取到的链接: {qqdocurl}")
                await process_b23_tv_url(bot, event, qqdocurl)
                return

        except json.JSONDecodeError as e:
            nonebot.logger.error(f"JSON 解析错误: {e}")
            await bot.send(event, "提取的 JSON 数据格式错误。")
            return

    # 处理常规 Bilibili 链接
    bv_pattern = re.compile(r'(BV[0-9A-Za-z]+)')
    if url.startswith('http://b23.tv/') or url.startswith('https://b23.tv/') or 'bilibili.com' in url:
        await process_b23_tv_url(bot, event, url)
        return


async def process_b23_tv_url(bot: Bot, event: Event, url: str):
    bv_pattern = re.compile(r'(BV[0-9A-Za-z]+)')
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=True) as response:
            final_url = str(response.url)
            bv_match = bv_pattern.search(final_url)
            if bv_match:
                bv_id = bv_match.group(1)
                await send_bilibili_info(bot, event, bv_id)
                return  # 添加这一行，确保处理完后返回

    # 检查常规 Bilibili 链接
    if 'bilibili.com' in url:
        bv_match = bv_pattern.search(url)
        if bv_match:
            bv_id = bv_match.group(1)
            await send_bilibili_info(bot, event, bv_id)
            return

    

def extract_bv_id(url: str) -> str:
    bv_pattern = re.compile(r'BV[0-9A-Za-z]+')
    bv_match = bv_pattern.search(url)
    return bv_match.group(0) if bv_match else None

async def send_bilibili_info(bot: Bot, event: Event, bv_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            data = await response.json()
            if data.get("code") == 0:
                video_data = data.get("data", {})
                pic_url = video_data.get("pic")
                title = video_data.get("title")
                owner_name = video_data.get("owner", {}).get("name")
                view_count = video_data.get("stat", {}).get("view")
                like_count = video_data.get("stat", {}).get("like")
                danmaku_count = video_data.get("stat", {}).get("danmaku")
                reply_count = video_data.get("stat", {}).get("reply")
                favorite_count = video_data.get("stat", {}).get("favorite")
                coin_count = video_data.get("stat", {}).get("coin")
                share_count = video_data.get("stat", {}).get("share")

                # 添加视频的 URL
                video_url = f"https://www.bilibili.com/video/{bv_id}"
                reply_message = (
                    f"标题: {title}\n"
                    f"UP主: {owner_name}\n"
                    f"播放量: {view_count}\n"
                    f"点赞: {like_count}\n"
                    f"弹幕: {danmaku_count}\n"
                    f"评论: {reply_count}\n"
                    f"收藏: {favorite_count}\n"
                    f"硬币: {coin_count}\n"
                    f"转发: {share_count}\n"
                    f"链接: {video_url}\n"  # 添加的行
                )

                if pic_url:
                    async with session.get(pic_url) as pic_response:
                        img_data = await pic_response.read()
                        img_base64 = base64.b64encode(img_data).decode("utf-8")
                        img_segment = MessageSegment.image(f"base64://{img_base64}")
                        await bot.send(event, MessageSegment.reply(event.message_id) + img_segment + reply_message)
                else:
                    await bot.send(event, reply_message)
            else:
                await bot.send(event, f"请求失败: {data.get('message')}")


# 插件元数据
__plugin_meta__ = {
    "name": "Bilibili信息插件",
    "description": "获取Bilibili视频信息和封面图",
    "usage": "发送包含Bilibili链接的消息"
}
