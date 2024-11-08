import traceback
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from playwright.async_api import async_playwright
import base64
from nonebot.log import logger
import re
from typing import List, Tuple
import markdown

__plugin_meta__ = PluginMetadata(
    name="喜报悲报生成器",
    description="生成喜报或悲报图片，支持图文混排、换行和Markdown语法",
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
            overflow-y: auto;
        }}
        
        .content {{
            font-size: 80px;
            font-weight: bold;
            color: {text_color};
            text-align: center;
            padding: 40px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            line-height: 1.5;
            max-width: 80%;
        }}
        
        .content p {{
            margin: 10px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .content img {{
            max-width: 300px;
            max-height: 200px;
            object-fit: contain;
            vertical-align: middle;
            margin: 0 10px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: inline-block;
        }}
        
        .content h1 {{
            font-size: 120px;
            margin: 20px 0;
        }}
        
        .content h2 {{
            font-size: 100px;
            margin: 18px 0;
        }}
        
        .content h3 {{
            font-size: 90px;
            margin: 16px 0;
        }}
        
        .content h4 {{
            font-size: 85px;
            margin: 14px 0;
        }}
        
        .content h5 {{
            font-size: 82px;
            margin: 12px 0;
        }}
        
        .content h6 {{
            font-size: 80px;
            margin: 10px 0;
        }}
        
        .content .line {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 10px 0;
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

def process_message(message: Message) -> List[Tuple[str, str]]:
    """处理消息，将文本和图片URL分离并按顺序保存"""
    elements = []
    current_text = ""
    
    for seg in message:
        if seg.type == "text":
            current_text += seg.data["text"]
        elif seg.type == "image":
            # 如果前面有文本且不以换行结尾，说明图片应该和文本在同一行
            if current_text and not current_text.endswith('\n'):
                elements.append(("inline_start", current_text))
                elements.append(("image", seg.data.get("url", "")))
                elements.append(("inline_end", ""))
                current_text = ""
            else:
                # 如果之前有文本，先保存文本
                if current_text:
                    elements.append(("text", current_text))
                    current_text = ""
                # 保存图片URL
                url = seg.data.get("url", "")
                if url:
                    elements.append(("image", url))
    
    # 保存最后的文本
    if current_text:
        elements.append(("text", current_text))
    
    return elements

def elements_to_html(elements: List[Tuple[str, str]]) -> str:
    """将元素列表转换为HTML内容"""
    html_parts = []
    in_line = False
    
    for type_, content in elements:
        if type_ == "text":
            # 将Markdown转换为HTML
            html_content = markdown.markdown(content)
            html_parts.append(html_content)
        elif type_ == "image":
            if in_line:
                html_parts.append(f'<img src="{content}" />')
            else:
                html_parts.append(f'<p><img src="{content}" /></p>')
        elif type_ == "inline_start":
            in_line = True
            # 将Markdown转换为HTML，但保持在同一行
            html_content = markdown.markdown(content)
            # 移除外层的<p>标签
            html_content = html_content.replace("<p>", "").replace("</p>", "")
            html_parts.append(f'<p>{html_content}')
        elif type_ == "inline_end":
            in_line = False
            html_parts.append('</p>')
    
    return ''.join(html_parts)

async def generate_news_image(content: List[Tuple[str, str]], is_happy: bool = True) -> bytes:
    """生成新闻图片"""
    logger.debug(f"开始生成{'喜' if is_happy else '悲'}报图片")
    
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
        content_html = elements_to_html(content)
        
        html_content = HTML_TEMPLATE.format(
            content=content_html,
            **theme_config
        )
        logger.debug("HTML模板生成成功")
        
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
            
            # 等待图片加载完成
            await page.wait_for_load_state("networkidle")
            
            # 等待内容渲染完成
            await page.wait_for_selector('.content')
            
            screenshot_bytes = await page.screenshot()
            logger.debug(f"截图成功，数据大小：{len(screenshot_bytes)} bytes")
            
            await browser.close()
            logger.debug("浏览器关闭成功")
            
            return screenshot_bytes
            
    except Exception as e:
        error_msg = f"生成图片时发生错误：{str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise Exception(error_msg)

async def process_news(message: Message, is_happy: bool = True):
    """处理新闻生成请求"""
    try:
        logger.info(f"开始处理{'喜' if is_happy else '悲'}报请求")
        
        elements = process_message(message)
        if not elements:
            return "请输入内容！"
        
        image_bytes = await generate_news_image(elements, is_happy)
        logger.debug("图片生成成功")
        
        base64_str = base64.b64encode(image_bytes).decode()
        logger.debug("Base64转换成功")
        
        msg = MessageSegment.image(f"base64://{base64_str}")
        logger.debug("消息构造成功")
        
        return msg
        
    except Exception as e:
        error_msg = f"处理请求时发生错误：{str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return f"生成失败，详细错误已记录到日志。错误信息：{str(e)}"

@happy_news.handle()
async def handle_happy_news(args: Message = CommandArg()):
    if not args:
        await happy_news.finish("请输入喜报内容！")
    
    result = await process_news(args, is_happy=True)
    await happy_news.finish(result)

@sad_news.handle()
async def handle_sad_news(args: Message = CommandArg()):
    if not args:
        await sad_news.finish("请输入悲报内容！")
    
    result = await process_news(args, is_happy=False)
    await sad_news.finish(result)