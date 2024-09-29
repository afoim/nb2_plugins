import re
import asyncio
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.plugin import PluginMetadata
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment, Message

__plugin_meta__ = PluginMetadata(
    name="网页截图",
    description="自动对以http/https开头的链接进行网页截图，支持全资源截屏和IPFS图片加载",
    usage="发送以http/https开头的链接即可触发，添加 '-a' 参数进行全资源截屏",
)

BLACKLIST = {
    "https://www.bilibili.com/video",
    "http://b23.tv",
}

url_pattern = re.compile(r'^(https?://\S+)(\s+-a)?$')

screenshot_matcher = on_message(priority=5)

async def wait_for_images(page):
    await page.evaluate('''
    () => {
        return new Promise((resolve) => {
            let images = Array.from(document.querySelectorAll('img'));
            let loadedImages = 0;

            if (images.length === 0) {
                resolve();
            }

            images.forEach((img) => {
                if (img.complete) {
                    loadedImages++;
                } else {
                    img.addEventListener('load', () => {
                        loadedImages++;
                        if (loadedImages === images.length) {
                            resolve();
                        }
                    });
                    img.addEventListener('error', () => {
                        loadedImages++;
                        if (loadedImages === images.length) {
                            resolve();
                        }
                    });
                }
            });

            if (loadedImages === images.length) {
                resolve();
            }
        });
    }
    ''')

async def take_screenshot(url: str, wait_for_all_resources: bool = False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale='zh-CN', timezone_id='Asia/Shanghai')
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if wait_for_all_resources:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.wait_for(wait_for_images(page), timeout=60.0)
        except PlaywrightTimeoutError:
            logger.warning(f"页面加载超时: {url}")
        except asyncio.TimeoutError:
            logger.warning(f"等待图片加载超时: {url}")
        
        # 即使超时，也尝试截图
        screenshot_bytes = await page.screenshot(full_page=True)
        await browser.close()
        return screenshot_bytes

@screenshot_matcher.handle()
async def handle_screenshot(bot: Bot, event: Event):
    message = event.get_message()
    message_text = message.extract_plain_text().strip()
    
    match = url_pattern.match(message_text)
    if not match:
        return
    
    url = match.group(1)
    if any(blocked in url for blocked in BLACKLIST):
        return
    
    wait_for_all_resources = bool(match.group(2))
    
    try:
        screenshot_bytes = await take_screenshot(url, wait_for_all_resources)
        reply = Message(MessageSegment.reply(event.message_id))
        reply += MessageSegment.image(screenshot_bytes)
        
        if wait_for_all_resources:
            reply
        
        await bot.send(event, reply)
    except Exception as e:
        logger.error(f"截图失败: {e}")
        await bot.send(event, f"截图失败: {e}")
        return