import os
import time
import base64
from pathlib import Path
import asyncio
import re
import traceback
import logging
import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.adapters import Bot, Event
from playwright.async_api import async_playwright

# 配置
DEBUG = False
VIEWPORT = {"width": 1920, "height": 1080}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# 日志函数
def log_info(msg, func="Unknown"): nonebot.logger.info(f"[{func}] {msg}")
def log_error(msg, func="Unknown"): nonebot.logger.error(f"[{func}] {msg}\n{traceback.format_exc()}")

class WebPreview:
    def __init__(self):
        self.playwright = None
        self.browser = None
        
    async def initialize(self):
        """初始化Playwright和浏览器"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=not DEBUG,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def wait_for_network_quiet(self, page, threshold=2, timeout=30000):
        """等待活动网络请求数降至阈值以下"""
        active_requests = set()

        def on_request(request):
            if not any(domain in request.url for domain in ['google-analytics', 'doubleclick.net']):
                active_requests.add(request)
                log_info(f"活动请求数: {len(active_requests)}", "network_wait")

        def on_response(response):
            if response.request in active_requests:
                active_requests.remove(response.request)
                log_info(f"活动请求数: {len(active_requests)}", "network_wait")

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            start_time = time.time() * 1000
            while (time.time() * 1000 - start_time) < timeout:
                if len(active_requests) <= threshold:
                    return True
                await asyncio.sleep(0.1)
            return False
        finally:
            page.remove_listener("request", on_request)
            page.remove_listener("response", on_response)

    async def simulate_scroll(self, page):
        """模拟页面滚动"""
        viewport_height = VIEWPORT["height"]
        scroll_height = await page.evaluate("""() => {
            return Math.max(
                document.documentElement.scrollHeight,
                document.body.scrollHeight,
                document.documentElement.clientHeight
            );
        }""")
        
        # 滚动步长为视口高度的一半
        step = viewport_height // 2
        for pos in range(0, scroll_height + step, step):
            await page.evaluate(f"window.scrollTo(0, {pos})")
            await asyncio.sleep(0.5)
        
        # 最后滚动回顶部
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

preview = WebPreview()

# URL匹配器
url_matcher = on_message(priority=5)

# 读取黑名单
def load_blacklist():
    blacklist_file = Path(__file__).parent / "web_ban" / "web_ban.txt"
    if blacklist_file.exists():
        with open(blacklist_file, "r") as f:
            patterns = [line.strip().replace("*", ".*") for line in f if line.strip()]
            return [re.compile(pattern) for pattern in patterns]
    return []

@url_matcher.handle()
async def handle_url(bot: Bot, event: Event):
    """处理URL消息"""
    message = str(event.get_message())
    
    # 检查是否是URL
    if not re.match(r'https?://', message):
        return

    # 检查黑名单
    if any(pattern.match(message) for pattern in load_blacklist()):
        return

    try:
        # 初始化
        await preview.initialize()
        
        # 创建新页面
        async with await preview.browser.new_context(
            viewport=VIEWPORT,
            user_agent=USER_AGENT
        ) as context:
            page = await context.new_page()
            
            # 导航到URL
            await page.goto(message, wait_until="domcontentloaded")
            
            # 等待网络活动减少
            if await preview.wait_for_network_quiet(page):
                # 模拟滚动
                await preview.simulate_scroll(page)
                
                # 截图
                screenshot = await page.screenshot(full_page=True, type='jpeg', quality=85)
                
                # 发送消息
                await bot.send(event, 
                    MessageSegment.reply(event.message_id) +
                    MessageSegment.image(f"base64://{base64.b64encode(screenshot).decode('utf-8')}")
                )
            else:
                await bot.send(event, "截图失败：网页加载超时")
                
    except Exception as e:
        log_error(f"处理URL失败: {str(e)}", "handle_url")
        await bot.send(event, f"截图失败: {str(e)}")

# 关闭时清理资源
nonebot.get_driver().on_shutdown(preview.cleanup)