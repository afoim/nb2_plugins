from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import aiohttp
import socket
import re

ipinfo = on_command("/ipinfo", priority=5)

@ipinfo.handle()
async def handle_ipinfo(bot: Bot, event: Event, args: Message = CommandArg()):
    target = args.extract_plain_text().strip()
    if not target:
        await ipinfo.finish(MessageSegment.reply(event.message_id) + "请提供要查询的IP地址或域名")
    
    # 去除 http:// 或 https:// 前缀
    target = re.sub(r'^https?://', '', target)
    
    # 如果存在路径,只保留域名部分
    target = target.split('/')[0]
    
    ip = await resolve_domain(target)
    if not ip:
        await ipinfo.finish(MessageSegment.reply(event.message_id) + "无法解析该域名或IP地址")
    
    info = await get_ip_info(ip, target)
    await ipinfo.finish(MessageSegment.reply(event.message_id) + info)

async def resolve_domain(host: str) -> str:
    try:
        addr_info = socket.getaddrinfo(host, None)
        for addr in addr_info:
            if addr[0] == socket.AF_INET6:
                return addr[4][0]
        for addr in addr_info:
            if addr[0] == socket.AF_INET:
                return addr[4][0]
    except socket.gaierror:
        return None

async def get_ip_info(ip: str, original_input: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://webapi-pc.meitu.com/common/ip_location?ip={ip}") as resp:
                data = await resp.json()

        if data['code'] != 0:
            return f"查询失败: {data.get('message', '未知错误')}"

        ip_data = data['data'].get(ip, {})
        
        return (
            f"查询接口: meitu.com\n"
            f"查询结果 (输入: {original_input}):\n"
            f"IP: {ip}\n"
            f"国家: {ip_data.get('nation', '')}\n"
            f"省份: {ip_data.get('province', '')}\n"
            f"城市: {ip_data.get('city', '')}\n"
            f"时区: {ip_data.get('time_zone', '')}\n"
            f"纬度: {ip_data.get('latitude', '')}\n"
            f"经度: {ip_data.get('longitude', '')}\n"
            f"ISP: {ip_data.get('isp', '')}\n"
        )
    except Exception as e:
        return f"查询失败: {str(e)}"
