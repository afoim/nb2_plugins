import os
import base64
import re
import aiohttp
import json
import shutil
import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment

# 设置 locale 为中文
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

# 创建 Bilibili URL 处理插件
bilibili_matcher = on_message(priority=5)

@bilibili_matcher.handle()
async def handle_bilibili_url(bot: Bot, event: Event):
    message = event.get_message()
    url = str(message)

    # 尝试解析 JSON 数据
    json_pattern = re.compile(r'\[CQ:json,data=(\{.*?\})\]')
    json_match = json_pattern.search(url)
    if json_match:
        json_data = json_match.group(1)
        json_data = json_data.replace('&#44;', ',').replace('&amp;', '&')

        try:
            data_dict = json.loads(json_data)
            qqdocurl = data_dict.get('meta', {}).get('detail_1', {}).get('qqdocurl')
            if qqdocurl:
                nonebot.logger.info(f"提取到的链接: {qqdocurl}")
                await process_b23_tv_url(bot, event, qqdocurl)
                return

        except json.JSONDecodeError as e:
            nonebot.logger.error(f"JSON 解析错误: {e}")
            # await bot.send(event, "提取的 JSON 数据格式错误。")
            return

    # 正则表达式匹配Bilibili的BV号或URL
    bv_pattern = re.compile(r'(BV[0-9A-Za-z]+|https?://b23.tv/[^\s]+|https?://www.bilibili.com/video/[^\s]+)')
    url_match = bv_pattern.search(url)
    
    if url_match:
        matched_url = url_match.group(0)
        await process_b23_tv_url(bot, event, matched_url)
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
                return

    if 'bilibili.com' in url:
        bv_match = bv_pattern.search(url)
        if bv_match:
            bv_id = bv_match.group(1)
            await send_bilibili_info(bot, event, bv_id)
            return

async def send_bilibili_info(bot: Bot, event: Event, bv_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/{bv_id}"  # 伪装 Referer 为视频页面
    }

    # 创建保存视频流的临时文件夹
    temp_dir = os.path.join(os.getcwd(), "bilibili_video_temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        nonebot.logger.info(f"创建临时文件夹: {temp_dir}")

    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            nonebot.logger.info(f"即将请求API，抓取视频详情")
            data = await response.json()
            if data.get("code") == 0:
                video_data = data.get("data", {})
                pic_url = video_data.get("pic")
                title = video_data.get("title")
                owner_name = video_data.get("owner", {}).get("name")
                cid = video_data.get("pages", [{}])[0].get("cid")

                view_count = format_number(video_data.get("stat", {}).get("view", 0))
                like_count = format_number(video_data.get("stat", {}).get("like", 0))
                danmaku_count = format_number(video_data.get("stat", {}).get("danmaku", 0))
                reply_count = format_number(video_data.get("stat", {}).get("reply", 0))
                favorite_count = format_number(video_data.get("stat", {}).get("favorite", 0))
                coin_count = format_number(video_data.get("stat", {}).get("coin", 0))
                share_count = format_number(video_data.get("stat", {}).get("share", 0))
                nonebot.logger.info(f"抓取视频详情成功")

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
                    f"链接: {video_url}\n"
                )
                nonebot.logger.info(f"格式化成功")

                if pic_url:
                    async with session.get(pic_url) as pic_response:
                        img_data = await pic_response.read()
                        img_base64 = base64.b64encode(img_data).decode("utf-8")
                        img_segment = MessageSegment.image(f"base64://{img_base64}")
                        await bot.send(event, MessageSegment.reply(event.message_id) + img_segment + reply_message)
                        nonebot.logger.info(f"已发送视频详情，开始获取视频流")
                else:
                    await bot.send(event, reply_message)

                if cid:
                    # 获取视频播放地址
                    play_url_api = f"https://api.bilibili.com/x/player/playurl?bvid={bv_id}&cid={cid}&qn=32"
                    async with session.get(play_url_api, headers=headers) as play_response:
                        play_data = await play_response.json()
                        if play_data.get("code") == 0:
                            durl = play_data.get("data", {}).get("durl", [{}])[0]
                            video_download_url = durl.get("url")

                            if video_download_url:
                                nonebot.logger.info(f"成功获取视频下载地址: {video_download_url}")

                                # 下载视频流并保存到本地
                                video_file_path = os.path.join(temp_dir, f"{bv_id}.mp4")
                                async with session.get(video_download_url, headers=headers) as video_response:
                                    if video_response.status == 200:
                                        video_data = await video_response.read()
                                        with open(video_file_path, "wb") as f:
                                            f.write(video_data)
                                        nonebot.logger.info(f"视频已保存至本地: {video_file_path}")

                                        # 将视频文件编码为 Base64
                                        with open(video_file_path, "rb") as f:
                                            video_base64 = base64.b64encode(f.read()).decode("utf-8")
                                            nonebot.logger.info(f"视频已编码为Base64，准备发送")

                                        
                                        # 发送 Base64 编码视频
                                        message = Message(f"[CQ:video,file=base64://{video_base64}]")
                                        await bot.send(event, message)
                                        nonebot.logger.info("视频发送完毕！")
                                        shutil.rmtree(temp_dir)
                                        nonebot.logger.info(f"已经删除临时文件夹：{temp_dir}")

                                    else:
                                        nonebot.logger.error(f"视频流请求失败，状态码: {video_response.status}")

                        else:
                            nonebot.logger.error(f"视频播放地址获取失败: {play_data.get('message')}")
            else:
                await bot.send(event, f"请求失败: {data.get('message')}")


def format_number(num: int) -> str:
    """将数字转换为带单位的格式，如 k、w"""
    if num >= 10000:
        return f"{num / 10000:.1f}w"
    elif num >= 1000:
        return f"{num / 1000:.1f}k"
    else:
        return str(num)
