from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from Wappalyzer import Wappalyzer, WebPage
import aiohttp

# 创建一个命令处理器
detect_tech = on_command("/detect_tech", priority=5)

@detect_tech.handle()
async def handle_detect_tech(bot: Bot, event: Event, args: Message = CommandArg()):
    # 提取原始消息 ID
    original_message_id = event.message_id
    domain = args.extract_plain_text().strip()
    
    if not domain:
        response = "请提供要查询的域名，例如：/detect_tech example.com"
    else:
        url = f"https://{domain}"
        try:
            tech_info = await get_technology_info(url)
            response = f"域名 {domain} 使用的技术:\n{tech_info}"
        except Exception as e:
            response = f"查询域名 {domain} 的技术栈信息时出错: {e}"

    # 创建引用消息
    reply_message = MessageSegment.reply(original_message_id) + response
    await detect_tech.finish(reply_message)

async def get_technology_info(url: str) -> str:
    wappalyzer = Wappalyzer.latest()

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                headers = dict(response.headers)
                webpage = WebPage(url, html=content, headers=headers)
                technologies = wappalyzer.analyze(webpage)

                # 将分析结果转换为字符串
                if isinstance(technologies, set):
                    tech_info = "\n".join(technologies)
                else:
                    tech_info = f"Unexpected type: {type(technologies)}, value: {technologies}"
                    
                return tech_info
            else:
                return f"无法访问 {url}，HTTP 状态码: {response.status}"
