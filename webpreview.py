import re
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.plugin import PluginMetadata
from playwright.async_api import async_playwright
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment, Message

__plugin_meta__ = PluginMetadata(
    name="网页截图",
    description="自动对以http/https开头的链接进行网页截图",
    usage="发送以http/https开头的链接即可触发",
)

BLACKLIST = {
    "https://www.bilibili.com/video",
    "http://b23.tv",
}

url_pattern = re.compile(r'^(https?://\S+)')
screenshot_matcher = on_message(priority=5)

@screenshot_matcher.handle()
async def handle_screenshot(bot: Bot, event: Event):
    message = event.get_message()
    message_text = message.extract_plain_text().strip()

    if not message_text or not (message_text.startswith('http://') or message_text.startswith('https://')):
        return

    match = url_pattern.match(message_text)
    
    if not match:
        return
    
    url = match.group(1)

    if any(blocked in url for blocked in BLACKLIST):
        return

    try:
        async with async_playwright() as p:
            # 启动浏览器，使用无头模式
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(locale='zh-CN', timezone_id='Asia/Shanghai')
            page = await context.new_page()

            # 导航到指定URL
            await page.goto(url, wait_until="networkidle")

            # 截取全页面截图
            screenshot_bytes = await page.screenshot(full_page=True)

            # 关闭浏览器
            await browser.close()

        # 创建并发送包含截图的消息
        reply = Message(MessageSegment.reply(event.message_id))
        reply += MessageSegment.image(screenshot_bytes)
        
        await bot.send(event, reply)
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return