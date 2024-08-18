import re
from nonebot import on_message
from nonebot.rule import to_me
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

# 在这里定义黑名单
BLACKLIST = {
    "https://www.bilibili.com/video",
    "http://b23.tv",
    # 添加更多需要屏蔽的域名
}

url_pattern = re.compile(r'^(https?://\S+)')
screenshot_matcher = on_message(priority=5)

@screenshot_matcher.handle()
async def handle_screenshot(bot: Bot, event: Event):
    # 获取消息内容并确保只处理文字消息
    message = event.get_message()
    message_text = message.extract_plain_text().strip()
    
    # 如果消息不包含文本或不是以http/https开头，直接返回
    if not message_text or not (message_text.startswith('http://') or message_text.startswith('https://')):
        return

    # 查找消息中的URL
    match = url_pattern.match(message_text)
    
    if not match:
        return
    
    url = match.group(1)
    
    # 检查URL是否在黑名单中
    if any(blocked in url for blocked in BLACKLIST):
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            screenshot_bytes = await page.screenshot(full_page=True)
            await browser.close()

        # 创建包含原始消息引用和截图的新消息
        reply = Message(MessageSegment.reply(event.message_id))
        reply += MessageSegment.image(screenshot_bytes)
        
        await bot.send(event, reply)
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return