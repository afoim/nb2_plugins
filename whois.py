from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import whois

whois_query = on_command("/whois", priority=5)

@whois_query.handle()
async def handle_whois(bot: Bot, event: Event, args: Message = CommandArg()):
    domain = args.extract_plain_text().strip()
    if not domain:
        await whois_query.finish("请提供要查询的域名")

    try:
        result = whois.whois(domain)
        if result:
            # 将所有属性转为字符串
            whois_info = "\n".join(f"{key}: {value}" for key, value in result.items() if value)
            response = f"域名信息 ({domain}):\n{whois_info}"
        else:
            response = f"无法获取域名 {domain} 的信息"
    except Exception as e:
        response = f"查询域名 {domain} 信息时出错: {e}"

    # 创建对原始消息的引用并附上查询结果
    reply_message = MessageSegment.reply(event.message_id) + response
    await bot.send(event, reply_message)
