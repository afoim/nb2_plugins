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

    async def optimize_page(self, page):
        """优化页面显示"""
        # 隐藏固定定位的元素（通常是弹窗或悬浮窗）
        await page.evaluate("""() => {
            const elements = document.querySelectorAll('*');
            for (const el of elements) {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'sticky') {
                    el.style.display = 'none';
                }
            }
        }""")
        
        # 等待一下以确保页面渲染完成
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

def parse_message(message: str):
    """解析消息，提取URL和等待时间"""
    # 匹配URL和可选的时间参数
    pattern = r'(https?://\S+)(?:\s+-(\d+))?'
    match = re.match(pattern, message.strip())
    if match:
        url = match.group(1)
        wait_time = int(match.group(2)) if match.group(2) else 0
        return url, wait_time
    return None, 0

@url_matcher.handle()
async def handle_url(bot: Bot, event: Event):
    """处理URL消息"""
    message = str(event.get_message())
    
    # 解析消息
    url, wait_time = parse_message(message)
    if not url:
        return

    # 检查黑名单
    if any(pattern.match(url) for pattern in load_blacklist()):
        return

    try:
        # 初始化
        await preview.initialize()
        
        # 创建新页面
        async with await preview.browser.new_context(
            viewport=VIEWPORT,
            user_agent=USER_AGENT,
            java_script_enabled=True
        ) as context:
            page = await context.new_page()
            
            # 设置更多选项来优化加载
            await page.set_extra_http_headers({"Accept-Language": "zh-CN,zh;q=0.9"})
            
            # 导航到URL并等待网络空闲
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 优化页面显示
            await preview.optimize_page(page)
            
            # 如果指定了等待时间，则等待
            if wait_time > 0:
                log_info(f"等待 {wait_time} 秒", "handle_url")
                await asyncio.sleep(wait_time)
            
            # 获取页面实际高度并设置视口
            page_dimensions = await page.evaluate("""() => {
                return {
                    width: Math.max(
                        document.documentElement.scrollWidth,
                        document.body.scrollWidth
                    ),
                    height: Math.max(
                        document.documentElement.scrollHeight,
                        document.body.scrollHeight
                    )
                }
            }""")
            
            # 调整视口大小以适应完整内容
            await page.set_viewport_size({
                "width": min(page_dimensions["width"], VIEWPORT["width"]),
                "height": page_dimensions["height"]
            })
            
            # 截图
            screenshot = await page.screenshot(
                full_page=True,
                type='jpeg',
                quality=85,
                scale="device"
            )
            
            # 发送消息
            await bot.send(event, 
                MessageSegment.reply(event.message_id) +
                MessageSegment.image(f"base64://{base64.b64encode(screenshot).decode('utf-8')}")
            )
                
    except Exception as e:
        log_error(f"处理URL失败: {str(e)}", "handle_url")
        # await bot.send(event, f"截图失败: {str(e)}")

# 关闭时清理资源
nonebot.get_driver().on_shutdown(preview.cleanup)