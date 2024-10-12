import os
import time
import base64
from pathlib import Path
import asyncio  # 导入 asyncio

# 设置 locale 为中文
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from playwright.async_api import async_playwright
import re

# 设置调试模式（True 为调试模式，False 为生产模式）
DEBUG = False  # 根据需要更改为 True 以启用调试模式

# 全局匹配 http/https 开头的消息
url_matcher = on_message(priority=5)

# 读取黑名单
def load_blacklist():
    blacklist = []
    blacklist_file = Path(__file__).parent / "web_ban" / "web_ban.txt"
    if blacklist_file.exists():
        with open(blacklist_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    blacklist.append(line.replace("*", ".*"))
    return [re.compile(pattern) for pattern in blacklist]

blacklist = load_blacklist()

@url_matcher.handle()
async def handle_url(bot: Bot, event: Event, state: T_State):
    message = event.get_message()
    url = str(message)

    # 重新加载黑名单
    blacklist = load_blacklist()

    # 检查 URL 是否在黑名单中
    if any(pattern.match(url) for pattern in blacklist):
        return

    if not re.match(r'https?://', url):
        return

    nonebot.logger.info("准备加载URL")

    # 创建新的任务来处理截图请求
    asyncio.create_task(process_url(bot, event, url))


async def process_url(bot: Bot, event: Event, url: str):
    start_time = time.time()  # 记录开始时间

    async with async_playwright() as p:
        nonebot.logger.info("启动Playwright")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # 根据 DEBUG 开关选择浏览器启动模式
        browser_args = []
        headless = not DEBUG  # 调试模式时为 False，其他情况为 True
        if DEBUG:
            browser_args = ["--no-sandbox", "--disable-setuid-sandbox", f"--display={os.environ.get('DISPLAY', ':0')}"]

        # 使用 Chromium 浏览器
        browser = await p.chromium.launch(headless=headless, args=browser_args)
        nonebot.logger.info("启动Chromium浏览器")
        
        context = await browser.new_context(
            user_agent=user_agent,
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9"
            }
        )
        nonebot.logger.info("创建新的浏览器上下文")
        page = await context.new_page()
        nonebot.logger.info("创建新的页面")

        try:
            nonebot.logger.info("开始导航到URL")
            await page.goto(url, timeout=60000)
            nonebot.logger.info("成功导航到URL，等待1s")
            await page.wait_for_timeout(1000)  # 等待1秒

            nonebot.logger.info("等待结束")

            # 模拟鼠标滚动到页面底部
            nonebot.logger.info("开始模拟滚动")
            scroll_height = await page.evaluate("document.body.scrollHeight")
            current_position = 0
            step = 500  # 每次滚动的像素数

            while current_position < scroll_height:
                await page.mouse.wheel(0, step)  # 向下滚动
                current_position += step
                await page.wait_for_timeout(50)  # 减少等待时间以提高效率

                # 更新滚动高度
                scroll_height = await page.evaluate("document.body.scrollHeight")

            nonebot.logger.info("滚动到底部，准备截图")
            
            # 截图并转换为Base64编码
            screenshot = await page.screenshot(full_page=True)
            nonebot.logger.info("获取全截图成功")
            base64_image = base64.b64encode(screenshot).decode('utf-8')
            nonebot.logger.info("已转为base64编码，截图成功，准备发送")

            # 发送截图
            await bot.send(event, MessageSegment.reply(event.message_id) + MessageSegment.image(f"base64://{base64_image}"))

        except Exception as e:
            nonebot.logger.error(f"截图过程中发生错误：{str(e)}")
        finally:
            nonebot.logger.info("关闭浏览器上下文和浏览器")
            await context.close()  # 确保关闭上下文
            await browser.close()

    end_time = time.time()  # 记录结束时间
    total_time = end_time - start_time
    nonebot.logger.info(f"总耗时: {total_time:.2f} 秒")

# 插件元数据
__plugin_meta__ = {
    "name": "网页截图插件",
    "description": "自动截取用户发送的URL网页",
    "usage": "发送包含http或https开头的URL即可触发截图"
}
