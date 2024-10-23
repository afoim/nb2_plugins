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
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# 自定义Playwright日志处理器
class PlaywrightLogHandler(logging.Handler):
    def emit(self, record):
        try:
            # 格式化日志消息
            msg = self.format(record)
            # 使用nonebot的日志记录器转发Playwright的日志
            if record.levelno >= logging.ERROR:
                nonebot.logger.error(f"[Playwright] {msg}")
            elif record.levelno >= logging.WARNING:
                nonebot.logger.warning(f"[Playwright] {msg}")
            else:
                nonebot.logger.info(f"[Playwright] {msg}")
        except Exception:
            self.handleError(record)

# 设置Playwright日志
def setup_playwright_logging():
    # 创建Playwright日志记录器
    playwright_logger = logging.getLogger('playwright')
    playwright_logger.setLevel(logging.DEBUG)
    
    # 创建并配置自定义处理器
    handler = PlaywrightLogHandler()
    handler.setLevel(logging.DEBUG)
    
    # 创建格式化器
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    playwright_logger.addHandler(handler)
    
    return playwright_logger

# 设置日志记录函数
def log_info(message, function_name="Unknown"):
    nonebot.logger.info(f"[{function_name}] {message}")

def log_error(message, function_name="Unknown", exc_info=None):
    error_msg = f"[{function_name}] {message}"
    if exc_info:
        error_msg += f"\n{traceback.format_exc()}"
    nonebot.logger.error(error_msg)

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
    else:
        log_info("黑名单文件不存在，使用空列表", "load_blacklist")
    return [re.compile(pattern) for pattern in blacklist]

# 全局 playwright 实例
playwright = None
browser = None
playwright_logger = None

async def initialize_playwright():
    global playwright, browser, playwright_logger
    function_name = "initialize_playwright"
    
    if playwright is None:
        log_info("开始初始化 Playwright", function_name)
        
        # 设置Playwright日志
        playwright_logger = setup_playwright_logging()
        
        playwright = await async_playwright().start()
        
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--enable-logging",
            "--v=1"
        ]
        if DEBUG:
            browser_args.append(f"--display={os.environ.get('DISPLAY', ':0')}")
        
        log_info(f"启动浏览器，参数：{browser_args}", function_name)
        browser = await playwright.chromium.launch(
            headless=not DEBUG,
            args=browser_args,
            chromium_sandbox=False,
        )
        log_info("浏览器启动完成", function_name)

async def wait_for_network_idle(page):
    function_name = "wait_for_network_idle"
    try:
        log_info("等待网络活动结束", function_name)
        await page.wait_for_load_state("networkidle", timeout=10000)
        log_info("网络活动已结束", function_name)
    except PlaywrightTimeoutError:
        log_info("等待网络空闲超时，继续处理", function_name)

async def wait_for_dynamic_content(page):
    function_name = "wait_for_dynamic_content"
    log_info("开始等待动态内容加载", function_name)
    
    try:
        result = await page.evaluate("""async () => {
            const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
            let status = [];
            
            // 等待图片加载
            try {
                const images = Array.from(document.getElementsByTagName('img'));
                status.push(`找到 ${images.length} 个图片元素`);
                
                let loadedImages = 0;
                await Promise.all(images.map(img => {
                    if (img.complete) {
                        loadedImages++;
                        return Promise.resolve();
                    }
                    return new Promise((resolve) => {
                        img.onload = img.onerror = () => {
                            loadedImages++;
                            resolve();
                        };
                    });
                }));
                status.push(`已加载 ${loadedImages} 个图片`);
            } catch (e) {
                status.push(`图片加载过程出错: ${e.message}`);
            }
            
            // 等待动画完成
            try {
                const elements = document.querySelectorAll('*');
                const animatingElements = Array.from(elements).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.animation !== 'none' || style.transition !== 'none';
                });
                
                status.push(`找到 ${animatingElements.length} 个带动画的元素`);
                if (animatingElements.length > 0) {
                    await delay(2000);
                    status.push('已等待动画完成');
                }
            } catch (e) {
                status.push(`动画检测过程出错: ${e.message}`);
            }
            
            // 等待滚动容器填充
            try {
                const container = document.querySelector('.scroll-container');
                if (container) {
                    status.push('找到滚动容器');
                    let attempts = 0;
                    while (container.children.length === 0 && attempts < 20) {
                        await delay(100);
                        attempts++;
                    }
                    status.push(`滚动容器已填充 ${container.children.length} 个子元素`);
                    await delay(2000);
                } else {
                    status.push('未找到滚动容器');
                }
            } catch (e) {
                status.push(`滚动容器检测过程出错: ${e.message}`);
            }
            
            await delay(1000);
            status.push('完成所有等待');
            
            return status;
        }""")
        
        for status_msg in result:
            log_info(status_msg, function_name)
            
    except Exception as e:
        log_error(f"等待动态内容时发生错误: {str(e)}", function_name, exc_info=True)

@url_matcher.handle()
async def handle_url(bot: Bot, event: Event, state: T_State):
    function_name = "handle_url"
    message = event.get_message()
    url = str(message)

    if any(pattern.match(url) for pattern in load_blacklist()):
        log_info("URL在黑名单中，已忽略", function_name)
        return

    if not re.match(r'https?://', url):
        return

    log_info("准备处理URL", function_name)
    asyncio.create_task(process_url(bot, event, url))

async def process_url(bot: Bot, event: Event, url: str):
    function_name = "process_url"
    start_time = time.time()
    log_info(f"开始处理URL: {url}", function_name)

    await initialize_playwright()

    try:
        log_info("创建浏览器上下文", function_name)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        log_info("创建新页面", function_name)
        page = await context.new_page()
        
        # 设置页面日志监听
        page.on("console", lambda msg: nonebot.logger.info(f"[Browser Console] {msg.text}"))
        page.on("pageerror", lambda err: nonebot.logger.error(f"[Browser Error] {err}"))
        page.on("request", lambda request: nonebot.logger.debug(f"[Browser Request] {request.method} {request.url}"))
        page.on("response", lambda response: nonebot.logger.debug(f"[Browser Response] {response.status} {response.url}"))

        log_info("开始导航到目标URL", function_name)
        response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        log_info(f"页面响应状态: {response.status}", function_name)

        await wait_for_network_idle(page)
        await wait_for_dynamic_content(page)

        # 模拟滚动
        log_info("开始模拟滚动", function_name)
        scroll_height = await page.evaluate("document.body.scrollHeight")
        for i in range(0, scroll_height, 100):  # 每次滚动100px
            await page.evaluate(f"window.scrollTo(0, {i})")
            await asyncio.sleep(0.1)  # 等待一会儿以便页面加载

        log_info("模拟滚动完成", function_name)

        # 设置 CSS 以防止字体加载
        await page.add_style_tag(content=""" 
            @font-face {
                font-family: 'CustomFont';
                src: local('Arial');
            }
            * {
                font-family: 'CustomFont', sans-serif !important;
            }
        """)

        log_info("获取页面尺寸", function_name)
        dimensions = await page.evaluate("""() => {
            return {
                width: Math.max(
                    document.documentElement.scrollWidth,
                    document.documentElement.clientWidth
                ),
                height: Math.max(
                    document.documentElement.scrollHeight,
                    document.documentElement.clientHeight
                )
            }
        }""")
        log_info(f"页面尺寸: {dimensions}", function_name)

        log_info("设置视口大小", function_name)
        await page.set_viewport_size({
            'width': dimensions['width'],
            'height': dimensions['height']
        })

        log_info("开始截图", function_name)
        screenshot = await page.screenshot(
            full_page=True,
            type='jpeg',
            quality=85,
            timeout=60000
        )
        log_info(f"截图完成，大小: {len(screenshot)} 字节", function_name)

        base64_image = base64.b64encode(screenshot).decode('utf-8')
        log_info("开始发送消息", function_name)
        await bot.send(event, MessageSegment.reply(event.message_id) + MessageSegment.image(f"base64://{base64_image}"))
        log_info("消息发送完成", function_name)

    except Exception as e:
        error_msg = f"截图过程中发生错误：{str(e)}"
        log_error(error_msg, function_name, exc_info=True)
        await bot.send(event, error_msg)
    finally:
        if 'context' in locals():
            log_info("关闭浏览器上下文", function_name)
            await context.close()

    end_time = time.time()
    total_time = end_time - start_time
    log_info(f"处理完成，总耗时：{total_time:.2f} 秒", function_name)

async def cleanup():
    function_name = "cleanup"
    global browser, playwright, playwright_logger
    if browser:
        log_info("关闭浏览器", function_name)
        await browser.close()
    if playwright:
        log_info("停止 Playwright", function_name)
        await playwright.stop()
    if playwright_logger:
        # 清理日志处理器
        for handler in playwright_logger.handlers[:]:
            playwright_logger.removeHandler(handler)
            handler.close()

nonebot.get_driver().on_shutdown(cleanup)