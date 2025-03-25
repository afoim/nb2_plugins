from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.params import CommandArg
from PIL import Image, ImageDraw
import io
import aiohttp
import re

# 创建命令处理器
circle_cmd = on_command("转圆形", priority=5)
rounded_cmd = on_command("转圆角", priority=5)

async def get_image_from_url(url: str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
    return Image.open(io.BytesIO(data))

def to_circle(img: Image.Image) -> Image.Image:
    # 创建一个正方形的画布
    size = min(img.size)
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    # 调整原图尺寸
    img = img.resize((size, size))
    output.paste(img, (0, 0))
    output.putalpha(mask)
    return output

def to_rounded(img: Image.Image, radius: int = 30) -> Image.Image:
    # 创建带圆角的图片
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius, fill=255)
    
    output = Image.new('RGBA', img.size, (0, 0, 0, 0))
    output.paste(img, (0, 0))
    output.putalpha(mask)
    return output

@circle_cmd.handle()
async def handle_circle(event: MessageEvent):
    # 检查是否为引用消息
    if not event.reply:
        await circle_cmd.finish("请引用包含图片的消息！")
    
    # 获取引用消息中的图片URL
    quoted_msg = event.reply.message
    img_url = None
    for seg in quoted_msg:
        if seg.type == "image":
            img_url = seg.data.get("url")
            break
    
    if not img_url:
        await circle_cmd.finish("引用的消息中没有图片！")
    
    # 处理图片
    try:
        img = await get_image_from_url(img_url)
        circle_img = to_circle(img)
        
        # 保存处理后的图片到字节流
        img_bytes = io.BytesIO()
        circle_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # 回复处理后的图片
        await circle_cmd.finish(MessageSegment.reply(event.message_id) + 
                              MessageSegment.image(img_bytes))
    except Exception as e:
        # await rounded_cmd.finish(f"处理图片时出错：{str(e)}")
        return

@rounded_cmd.handle()
async def handle_rounded(event: MessageEvent):
    # 检查是否为引用消息
    if not event.reply:
        await rounded_cmd.finish("请引用包含图片的消息！")
    
    # 获取引用消息中的图片URL
    quoted_msg = event.reply.message
    img_url = None
    for seg in quoted_msg:
        if seg.type == "image":
            img_url = seg.data.get("url")
            break
    
    if not img_url:
        await rounded_cmd.finish("引用的消息中没有图片！")
    
    # 处理图片
    try:
        img = await get_image_from_url(img_url)
        rounded_img = to_rounded(img)
        
        # 保存处理后的图片到字节流
        img_bytes = io.BytesIO()
        rounded_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # 回复处理后的图片
        await rounded_cmd.finish(MessageSegment.reply(event.message_id) + 
                               MessageSegment.image(img_bytes))
    except Exception as e:
        # await rounded_cmd.finish(f"处理图片时出错：{str(e)}")
        return