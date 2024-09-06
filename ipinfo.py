from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import aiohttp
import socket
import ipaddress
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
            async with session.get(f"http://ip-api.com/json/{ip}?lang=zh-CN") as resp:
                data = await resp.json()

        cdn_info = check_cdn_ip(ip)

        return (
            f"查询接口: ip-api.com\n"
            f"查询结果 (输入: {original_input}):\n"
            f"IP: {data.get('query', '')}\n"
            f"国家: {data.get('country', '')}\n"
            f"地区: {data.get('regionName', '')}\n"
            f"城市: {data.get('city', '')}\n"
            f"时区: {data.get('timezone', '')}\n"
            f"ISP: {data.get('isp', '')}\n"
            f"组织: {data.get('org', '')}\n"
            f"AS: {data.get('as', '')}\n"
            f"纬度: {data.get('lat', '')}\n"
            f"经度: {data.get('lon', '')}\n"
            f"邮政编码: {data.get('zip', '')}\n"
            f"CDN提供商: {cdn_info}"
        )
    except Exception as e:
        return f"查询失败: {str(e)}"

def check_cdn_ip(ip: str) -> str:
    ip_obj = ipaddress.ip_address(ip)
    cdn_ranges = {
        'Cloudflare': [
            '173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22',
            '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20',
            '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13',
            '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22',
            '2400:cb00::/32', '2606:4700::/32', '2803:f800::/32', '2405:b500::/32',
            '2405:8100::/32', '2a06:98c0::/29', '2c0f:f248::/32'
        ],
        '腾讯云': [
            '183.3.254.0/24', '58.250.143.0/24', '58.251.121.0/24', '59.36.120.0/24',
            '61.151.163.0/24', '111.161.109.0/24', '123.151.76.0/24', '101.227.163.0/24',
            '140.207.120.0/24', '180.163.22.0/24', '116.128.128.0/24', '125.39.46.0/24',
            '223.166.151.0/24'
        ],
        '百度云': [
            '111.63.51.0/24', '221.195.34.0/24', '183.230.70.0/24', '183.214.156.0/24',
            '223.112.198.0/24', '58.216.2.0/24', '218.98.44.0/24', '59.38.112.0/24',
            '106.122.248.0/24', '163.177.8.0/24', '61.136.173.0/24', '120.221.136.0/24',
            '150.138.248.0/24', '27.221.124.0/24', '183.131.62.0/24', '120.199.69.0/24',
            '120.221.29.0/24', '150.138.138.0/24', '27.221.27.0/24', '42.81.93.0/24',
            '58.215.118.0/24', '36.42.75.0/24', '111.177.3.0/24', '111.47.227.0/24',
            '111.177.6.0/24', '119.36.164.0/24', '112.84.34.0/24', '223.111.127.0/24',
            '58.20.204.0/24'
        ],
        '阿里云': [
            '47.244.0.0/28', '47.106.0.0/28', '106.15.0.0/28', '101.132.0.0/28',
            '119.23.0.0/28', '101.200.0.0/28', '114.215.0.0/28', '47.52.0.0/28',
            '198.11.0.0/28', '47.88.0.0/28', '161.117.0.0/28', '47.246.0.0/28'
        ],
        '加速乐/创宇云': [
            '113.107.238.0/24', '106.42.25.0/24', '183.222.96.0/24', '117.21.219.0/24',
            '116.55.250.0/24', '111.202.98.0/24', '111.13.147.0/24', '122.228.238.0/24',
            '58.58.81.0/24', '1.31.128.0/24', '123.155.158.0/24', '106.119.182.0/24',
            '113.207.76.0/24', '117.23.61.0/24', '118.212.233.0/24', '111.47.226.0/24',
            '219.153.73.0/24', '113.200.91.0/24', '203.90.247.0/24', '183.110.242.0/24',
            '185.254.242.0/24', '116.211.155.0/24', '116.140.35.0/24', '103.40.7.0/24',
            '1.255.41.0/24', '112.90.216.0/24', '1.255.100.0/24'
        ],
        '360CDN/奇安信': ['36.27.212.0/24', '123.129.232.0/24'],
        '牛盾云安全': [
            '113.31.27.0/24', '222.186.19.0/24', '122.226.182.0/24', '36.99.18.0/24',
            '123.133.84.0/24', '221.204.202.0/24', '42.236.6.0/24', '61.130.28.0/24',
            '61.174.9.0/24', '223.94.66.0/24', '222.88.94.0/24', '61.163.30.0/24',
            '223.94.95.0/24', '223.112.227.0/24', '183.250.179.0/24', '120.241.102.0/24',
            '125.39.5.0/24', '124.193.166.0/24', '122.70.134.0/24', '111.6.191.0/24',
            '122.228.198.0/24', '121.12.98.0/24', '60.12.166.0/24', '118.180.50.0/24',
            '183.203.7.0/24', '61.133.127.0/24', '113.7.183.0/24', '210.22.63.0/24',
            '60.221.236.0/24', '122.227.237.0/24'
        ],
        'LightCDN': [
        '38.54.24.160/27', '2404:a140:26:2::/64',
        '38.54.7.0/27', '2404:A140:b:1::/64',
        '154.206.65.0/24', '2404:a140:15:3::/64',
        '38.54.120.0/24', '2404:A140:9:1::/64',
        '38.60.209.0/24', '2404:A140:3:B::1/64',
        '38.54.53.0/26', '2404:A140:20:5::/64',
        '38.54.47.0/25', '2404:A140:5:B::/64',
        '38.54.26.0/26', '2404:A140:2C:3::/64',
        '38.54.12.192/27', 
        '38.54.123.192/26',
        '38.60.158.0/24',
        '38.54.35.32/27',
        '38.54.106.0/24',
        '38.54.51.128/27',
        '59.153.158.0/26',
        '38.54.40.0/24',
        '175.176.193.0/25',
        '38.54.98.0/26',
        '38.60.150.0/24',
        '38.54.1.160/27',
        '103.151.120.0/25',
        '38.54.65.0/26',
        '38.54.5.0/26',
        '38.54.9.0/27',
        '59.153.156.0/26',
        '103.198.201.64/26',
        '38.54.72.0/26',
        '185.23.183.0/25',
        '59.153.159.128/26',
        '38.54.3.64/26',
        '38.54.63.0/24',
        '103.198.202.0/26'
    ]
    }
    for cdn, ranges in cdn_ranges.items():
        if any(ip_obj in ipaddress.ip_network(cidr, strict=False) for cidr in ranges):
            return cdn
    return '未知或无'
