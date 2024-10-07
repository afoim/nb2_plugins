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

async def smooth_scroll(page):
    logger.info("开始执行平滑滚动")
    await page.evaluate('''
    () => {
        return new Promise((resolve) => {
            let totalHeight = 0;
            const distance = 100;
            const timer = setInterval(() => {
                const scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;
                console.log(`Scrolled to ${totalHeight}px`);

                if(totalHeight >= scrollHeight){
                    clearInterval(timer);
                    console.log('Scrolling finished');
                    resolve();
                }
            }, 100);
        });
    }
    ''')
    logger.info("平滑滚动完成")

async def take_screenshot(url: str, wait_for_all_resources: bool = False):
    logger.info(f"开始截图过程，URL: {url}, 等待所有资源: {wait_for_all_resources}")
    async with async_playwright() as p:
        logger.info("启动 Playwright")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            viewport={'width': 1280, 'height': 800},
            is_mobile=False
        )
        
        page = await context.new_page()
        logger.info("创建新页面")

        try:
            logger.info(f"正在加载页面: {url}")
            await asyncio.wait_for(
                page.goto(url, wait_until="domcontentloaded"),
                timeout=30.0
            )
            logger.info("等待网络空闲")
            await asyncio.wait_for(
                page.wait_for_load_state('networkidle'),
                timeout=30.0
            )

            if wait_for_all_resources:
                logger.info("等待所有资源，开始滚动")
                await asyncio.wait_for(
                    smooth_scroll(page),
                    timeout=30.0
                )
                logger.info("滚动完成，再次等待网络空闲")
                await asyncio.wait_for(
                    page.wait_for_load_state('networkidle'),
                    timeout=30.0
                )

            logger.info("开始截图")
            screenshot_bytes = await page.screenshot(full_page=True)
            logger.info("截图完成")
        except asyncio.TimeoutError:
            logger.warning(f"页面加载超时: {url}")
            logger.info("尝试对已加载内容进行截图")
            screenshot_bytes = await page.screenshot(full_page=True)
        except Exception as e:
            logger.error(f"截图过程中发生错误: {e}")
            screenshot_bytes = None
        finally:
            logger.info("关闭浏览器")
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
    logger.info(f"提取的URL: {url}")

    if any(blocked in url for blocked in BLACKLIST):
        logger.info(f"URL在黑名单中: {url}")
        return

    wait_for_all_resources = bool(match.group(2))
    logger.info(f"等待所有资源: {wait_for_all_resources}")

    try:
        logger.info("开始调用截图函数")
        screenshot_bytes = await take_screenshot(url, wait_for_all_resources)
        if screenshot_bytes:
            logger.info("截图成功，准备发送")
            reply = Message(MessageSegment.reply(event.message_id))
            reply += MessageSegment.image(screenshot_bytes)
            await bot.send(event, reply)
            logger.info("截图已发送")
        else:
            logger.warning("截图失败，返回为None")
            await bot.send(event, "截图失败，请检查网址是否正确或稍后重试。")
    except Exception as e:
        logger.error(f"在handle_screenshot中发生异常: {e}")
        await bot.send(event, f"截图失败: {e}")
        return