from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
import base64
from playwright.async_api import async_playwright

# 定义命令
hr = on_command("/hr")
vr = on_command("/vr")

async def fetch_image(url: str) -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # 启用 request 拦截器
        await page.route("**/*", lambda route, request: route.continue_())
        
        # 捕获图片响应
        response = await page.goto(url)
        content = await response.body()
        
        await browser.close()
        return content

@hr.handle()
async def handle_hr(bot: Bot, event: Event):
    image_url = "http://127.0.0.1:8011/h.php"
    image_bytes = await fetch_image(image_url)
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    reply = MessageSegment.reply(event.message_id) + MessageSegment.image(f"base64://{base64_image}")
    await hr.finish(reply)

@vr.handle()
async def handle_vr(bot: Bot, event: Event):
    image_url = "http://127.0.0.1:8011/v.php"
    image_bytes = await fetch_image(image_url)
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    reply = MessageSegment.reply(event.message_id) + MessageSegment.image(f"base64://{base64_image}")
    await vr.finish(reply)
