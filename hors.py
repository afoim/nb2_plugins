import traceback
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from playwright.async_api import async_playwright
import base64
from nonebot.log import logger

__plugin_meta__ = PluginMetadata(
    name="喜报悲报生成器",
    description="生成喜报或悲报图片",
    usage="喜报/悲报 <内容>",
    type="application",
    homepage="",
    supported_adapters={"~onebot.v11"},
)

# 注册命令
happy_news = on_command("喜报", priority=5, block=True)
sad_news = on_command("悲报", priority=5, block=True)

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            width: 1600px;
            height: 900px;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: {bg_color};
            background-image: linear-gradient(45deg, rgba(255,255,255,0.2) 25%, 
                transparent 25%, transparent 50%, rgba(255,255,255,0.2) 50%, 
                rgba(255,255,255,0.2) 75%, transparent 75%, transparent);
            background-size: 50px 50px;
            overflow: hidden;
        }}
        
        .container {{
            width: 90%;
            height: 80%;
            border: 20px double {border_color};
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: white;
            position: relative;
        }}
        
        .content {{
            font-size: 80px;
            font-weight: bold;
            color: {text_color};
            text-align: center;
            padding: 40px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            line-height: 1.5;
            white-space: pre-line;  /* 支持换行 */
            max-width: 80%;
        }}
        
        .seal {{
            position: absolute;
            bottom: 50px;
            right: 50px;
            width: 150px;
            height: 150px;
            border: 5px solid {seal_color};
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: {seal_color};
            font-size: 40px;
            transform: rotate(-30deg);
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">{content}</div>
        <div class="seal">{seal_text}</div>
    </div>
</body>
</html>
"""

async def generate_news_image(content: str, is_happy: bool = True) -> bytes:
    logger.debug(f"开始生成{'喜' if is_happy else '悲'}报图片，内容：{content}")
    
    # 设置颜色主题
    theme = {
        "happy": {
            "bg_color": "#FF4D4D",
            "border_color": "#FFD700",
            "text_color": "#FF0000",
            "seal_color": "#FF0000",
            "seal_text": "喜讯"
        },
        "sad": {
            "bg_color": "#4682B4",
            "border_color": "#000000",
            "text_color": "#000000",
            "seal_color": "#000000",
            "seal_text": "悲讯"
        }
    }
    
    theme_config = theme["happy"] if is_happy else theme["sad"]
    
    try:
        # 处理内容中的换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 生成HTML内容
        html_content = HTML_TEMPLATE.format(
            content=content,
            **theme_config
        )
        logger.debug("HTML模板生成成功")
        
        # 使用Playwright生成图片
        async with async_playwright() as p:
            logger.debug("启动 Playwright")
            browser = await p.chromium.launch(
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            logger.debug("浏览器启动成功")
            
            page = await browser.new_page(viewport={"width": 1600, "height": 900})
            logger.debug("页面创建成功")
            
            await page.set_content(html_content)
            logger.debug("HTML内容设置成功")
            
            # 等待内容渲染完成
            await page.wait_for_selector('.content')
            
            # 直接获取图片的字节数据
            screenshot_bytes = await page.screenshot()
            logger.debug(f"截图成功，数据大小：{len(screenshot_bytes)} bytes")
            
            await browser.close()
            logger.debug("浏览器关闭成功")
            
            return screenshot_bytes
            
    except Exception as e:
        error_msg = f"生成图片时发生错误：{str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise Exception(error_msg)

async def process_news(content: str, is_happy: bool = True):
    try:
        logger.info(f"开始处理{'喜' if is_happy else '悲'}报请求：{content}")
        
        # 生成图片
        image_bytes = await generate_news_image(content, is_happy)
        logger.debug("图片生成成功")
        
        # 转换为base64
        base64_str = base64.b64encode(image_bytes).decode()
        logger.debug("Base64转换成功")
        
        # 构造消息
        msg = MessageSegment.image(f"base64://{base64_str}")
        logger.debug("消息构造成功")
        
        return msg
        
    except Exception as e:
        error_msg = f"处理请求时发生错误：{str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return f"生成失败，详细错误已记录到日志。错误信息：{str(e)}"

@happy_news.handle()
async def handle_happy_news(args: Message = CommandArg()):
    content = str(args).strip()  # 使用 str() 而不是 extract_plain_text() 来保留换行符
    if not content:
        await happy_news.finish("请输入喜报内容！")
    
    result = await process_news(content, is_happy=True)
    await happy_news.finish(result)

@sad_news.handle()
async def handle_sad_news(args: Message = CommandArg()):
    content = str(args).strip()  # 使用 str() 而不是 extract_plain_text() 来保留换行符
    if not content:
        await sad_news.finish("请输入悲报内容！")
    
    result = await process_news(content, is_happy=False)
    await sad_news.finish(result)