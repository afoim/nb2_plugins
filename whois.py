from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import whois

whois_query = on_command("/whois", priority=5)

# 创建翻译字典
translation_dict = {
    'domain_name': '域名',
    'registrar': '注册商',
    'whois_server': 'WHOIS服务器',
    'referral_url': '推荐链接',
    'updated_date': '更新日期',
    'creation_date': '创建日期',
    'expiration_date': '到期日期',
    'name_servers': '名称服务器（DS解析）',
    'status': '状态',
    'emails': '邮箱',
    'dnssec': 'DNSSEC',
    'print_date': '打印日期',
    'last_update': '最后更新',
    'name': '姓名',
    'org': '组织',
    'address': '地址',
    'city': '城市',
    'state': '省份',
    'registrant_postal_code': '邮政编码',
    'country': '国家',
    'registrant_name': '注册人姓名',
    'registrant_address': '注册人地址',
    'registrant_phone_number': '注册人电话',
    'registrant_email': '注册人邮箱',
}

@whois_query.handle()
async def handle_whois(bot: Bot, event: Event, args: Message = CommandArg()):
    domain = args.extract_plain_text().strip()
    if not domain:
        await whois_query.finish("请提供要查询的域名")

    try:
        result = whois.whois(domain)
        if result:
            # 将所有属性转为中文字符串
            whois_info = "\n".join(
                f"{translation_dict.get(key, key)}: {value}" 
                for key, value in result.items() if value
            )
            response = f"域名信息 ({domain}):\n{whois_info}"
        else:
            response = f"无法获取域名 {domain} 的信息"
    except Exception as e:
        response = f"查询域名 {domain} 信息时出错: {e}"

    # 创建对原始消息的引用并附上查询结果
    reply_message = MessageSegment.reply(event.message_id) + response
    await bot.send(event, reply_message)
