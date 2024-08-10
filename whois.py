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
            # 处理状态
            status = result.status
            if isinstance(status, list):
                status = ', '.join(status)
            elif isinstance(status, str):
                status = status.replace(',', ', ')
            
            # 处理 DNS 服务器
            dns_servers = result.name_servers
            if isinstance(dns_servers, list):
                dns_servers = ', '.join(dns_servers)
            elif isinstance(dns_servers, str):
                dns_servers = dns_servers.replace(',', ', ')

            response = (
                f"域名信息 ({domain}):\n"
                f"注册商: {result.registrar}\n"
                f"注册时间: {result.creation_date}\n"
                f"到期时间: {result.expiration_date}\n"
                f"DNS服务器: {dns_servers}\n"
                f"状态: {status}"
            )
        else:
            response = f"无法获取域名 {domain} 的信息"
    except Exception as e:
        response = f"查询域名 {domain} 信息时出错: {e}"

    # 创建对原始消息的引用并附上查询结果
    reply_message = MessageSegment.reply(event.message_id) + response
    await bot.send(event, reply_message)
