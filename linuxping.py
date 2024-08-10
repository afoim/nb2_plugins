from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
import asyncio
import re
import socket

ping = on_command("/ping", priority=5)

@ping.handle()
async def handle_ping(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    target = args.extract_plain_text().strip()
    if not target:
        await ping.finish(MessageSegment.reply(event.message_id) + "请提供要ping的目标域名或IP地址")
    
    if not is_valid_host(target):
        await ping.finish(MessageSegment.reply(event.message_id) + "无效的域名或IP地址")
    
    if is_domain(target):
        ipv4 = await resolve_domain(target, socket.AF_INET)
        ipv6 = await resolve_domain(target, socket.AF_INET6)
        result_v4 = await run_ping(ipv4, "-4") if ipv4 else "无法解析IPv4地址"
        result_v6 = await run_ping(ipv6, "-6") if ipv6 else "无法解析IPv6地址"
        result = f"IPv4结果:{result_v4}\n\nIPv6结果:{result_v6}"
    else:
        result = await run_ping(target)
    
    response = f"发起Ping请求主机：安徽合肥（移动）\nPing 结果 (目标: {target}):\n\n{result}"
    await ping.finish(MessageSegment.reply(event.message_id) + response)

def is_valid_host(host):
    ip_pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
    domain_pattern = r"^[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+$"
    return re.match(ip_pattern, host) or re.match(domain_pattern, host)

def is_domain(host):
    domain_pattern = r"^[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+$"
    return re.match(domain_pattern, host)

async def resolve_domain(host, address_family):
    try:
        return socket.getaddrinfo(host, None, address_family)[0][4][0]
    except socket.gaierror:
        return None

async def run_ping(target, version_flag=""):
    try:
        process = await asyncio.create_subprocess_shell(
            f"ping {version_flag} -c 5 {target}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if stdout:
            return f"\n{stdout.decode().strip()}"
        if stderr:
            return f"Error: {stderr.decode().strip()}"
    except Exception as e:
        return f"执行ping命令时发生错误: {str(e)}"
