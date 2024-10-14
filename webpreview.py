import os
import time
import base64
from pathlib import Path
import asyncio
import re

import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# 设置 locale 为中文
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

# 设置调试模式（True 为调试模式，False 为生产模式）
DEBUG = False

# 全局匹配 http/https 开头的消息
url_matcher = on_message(priority=5)

# 读取黑名单
def load_blacklist():
    blacklist = []
    blacklist_file = Path(__file__).parent / "web_ban" / "web_ban.txt"
    if blacklist_file.exists():
        with open(blacklist_file, "r") as f:
            blacklist = [line.strip().replace("*", ".*") for line in f if line.strip()]
    return [re.compile(pattern) for pattern in blacklist]

# 全局 playwright 实例
playwright = None
browser = None

async def initialize_playwright():
    global playwright, browser
    if playwright is None:
        playwright = await async_playwright().start()
        browser_args = ["--no-sandbox", "--disable-setuid-sandbox"]
        if DEBUG:
            browser_args.append(f"--display={os.environ.get('DISPLAY', ':0')}")
        browser = await playwright.chromium.launch(headless=not DEBUG, args=browser_args)

@url_matcher.handle()
async def handle_url(bot: Bot, event: Event, state: T_State):
    message = event.get_message()
    url = str(message)

    # 检查 URL 是否在黑名单中
    if any(pattern.match(url) for pattern in load_blacklist()):
        return

    if not re.match(r'https?://', url):
        return

    nonebot.logger.info("准备加载 URL")

    # 创建新的任务来处理截图请求
    asyncio.create_task(process_url(bot, event, url))

async def process_url(bot: Bot, event: Event, url: str):
    start_time = time.time()

    await initialize_playwright()

    try:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        context = await browser.new_context(
            user_agent=user_agent,
            extra_http_headers={"Accept-Language": "zh-CN,zh;q=0.9"}
        )
        nonebot.logger.info("创建了新的浏览器上下文")
        
        page = await context.new_page()
        nonebot.logger.info("创建了新的页面")

        # 使用更宽松的加载策略
        try:
            await page.goto(url, timeout=30000, wait_until='domcontentloaded')
        except PlaywrightTimeoutError:
            nonebot.logger.warning("页面加载超时，但继续处理")

        nonebot.logger.info("开始处理页面")

        # 实现渐进式滚动并等待图片加载
        nonebot.logger.info("开始渐进式滚动并等待图片加载")
        await page.evaluate("""
            async () => {
                const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                
                const scrollStep = async () => {
                    const scrollHeight = document.documentElement.scrollHeight;
                    const viewportHeight = window.innerHeight;
                    let scrollTop = 0;
                    
                    while (scrollTop < scrollHeight) {
                        window.scrollTo(0, scrollTop);
                        await delay(100);  // 等待一小段时间让新内容加载
                        
                        // 检查可见区域内的图片并等待它们加载
                        const visibleImages = Array.from(document.querySelectorAll('img')).filter(img => {
                            const rect = img.getBoundingClientRect();
                            return rect.top >= 0 && rect.bottom <= viewportHeight;
                        });
                        
                        await Promise.all(visibleImages.map(img => {
                            if (img.complete) return Promise.resolve();
                            return new Promise(resolve => {
                                img.onload = img.onerror = resolve;
                            });
                        }));
                        
                        scrollTop += viewportHeight / 2;  // 滚动半个视口高度
                    }
                    
                    window.scrollTo(0, 0);  // 滚回顶部
                };
                
                await scrollStep();
            }
        """)
        nonebot.logger.info("渐进式滚动和图片加载完成")

        # 额外等待一小段时间，确保所有内容都已渲染
        await page.wait_for_timeout(2000)

        # 截图并转换为Base64编码
        screenshot = await page.screenshot(full_page=True)
        nonebot.logger.info("成功捕获全页面截图")
        base64_image = base64.b64encode(screenshot).decode('utf-8')
        nonebot.logger.info("已转换为base64编码，准备发送")

        # 发送截图
        await bot.send(event, MessageSegment.reply(event.message_id) + MessageSegment.image(f"base64://{base64_image}"))

    except Exception as e:
        nonebot.logger.error(f"截图过程中发生错误：{str(e)}")
    finally:
        nonebot.logger.info("关闭浏览器上下文")
        await context.close()

    end_time = time.time()
    total_time = end_time - start_time
    nonebot.logger.info(f"总耗时：{total_time:.2f} 秒")

# 插件元数据
__plugin_meta__ = {
    "name": "网页截图插件",
    "description": "自动截取用户发送的URL网页，支持懒加载内容",
    "usage": "发送包含http或https开头的URL即可触发截图"
}

# 清理函数，在机器人关闭时调用
async def cleanup():
    global browser, playwright
    if browser:
        await browser.close()
    if playwright:
        await playwright.stop()

# 注册清理函数，在退出时调用
nonebot.get_driver().on_shutdown(cleanup)