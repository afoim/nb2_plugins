from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import asyncio
import socket
import nonebot

openport = on_command("/openport", priority=5)

TIMEOUT = 1  # 用于端口扫描的超时时间（秒）

PORT_USAGE = {
    21: "FTP文件服务器",
    22: "SSH",
    23: "Telnet",
    25: "SMTP邮件接口",
    53: "DNS服务器",
    80: "HTTP网站",
    110: "POP3电子邮件接收",
    119: "NNTP网络新闻传送",
    123: "NTP时间服务器",
    135: "Microsoft RPC",
    143: "IMAP邮件接口",
    161: "SNMP简单网络管理协议",
    194: "IRC因特网中继聊天",
    443: "HTTPS网站",
    445: "Microsoft-DS微软共享接口",
    465: "SMTPS更安全的邮件接口",
    993: "IMAPS更安全的邮件接口",
    995: "POP3S更安全的邮件接口",
    1433: "Microsoft SQL Server微软SQL数据库",
    1521: "Oracle Database甲骨文数据库",
    3306: "MySQL数据库",
    3389: "RDP微软远程桌面",
    5432: "PostgreSQL数据库",
    5244: "AList网盘",
    5900: "VNC远程桌面",
    6379: "Redis数据库",
    8080: "用于建站或代理网站",
    25565: "MC服务器"
}

# 用于跟踪扫描任务的状态
scan_in_progress = False

@openport.handle()
async def handle_openport(bot: Bot, event: Event, args: Message = CommandArg()):
    global scan_in_progress
    
    if scan_in_progress:
        await openport.finish(MessageSegment.reply(event.message_id) + "已有扫描任务正在进行中，请稍后再试。")
    
    arg_list = args.extract_plain_text().strip().split()
    if len(arg_list) < 1:
        await openport.finish(MessageSegment.reply(event.message_id) + "请提供要测试的IP地址或域名")
    
    target = arg_list[0]
    scan_all = openport
    
    # 解析端口范围
    start_port, end_port = 1, 65535
    if len(arg_list) > 2:
        try:
            port_range = arg_list[2].split('-')
            start_port = int(port_range[0])
            end_port = int(port_range[1]) if len(port_range) > 1 else start_port
        except ValueError:
            await openport.finish(MessageSegment.reply(event.message_id) + "端口范围格式无效，请使用 'start-end' 或单个端口号")
    
    ip = await resolve_domain(target)
    if not ip:
        await openport.finish(MessageSegment.reply(event.message_id) + "无法解析该域名或IP地址")

    scan_in_progress = True
    try:
        if scan_all:
            await openport.send(MessageSegment.reply(event.message_id) + f"开始扫描 {target} 的端口 {start_port}-{end_port}，这可能需要一些时间...")
            nonebot.logger.info(f"对{target}的端口扫描已启动，范围：{start_port}-{end_port}")
            results = await check_port_range(ip, start_port, end_port)
        
        open_ports = [port for port, is_open in results.items() if is_open]
        
        if open_ports:
            open_ports_str = format_port_ranges(open_ports)
            usages = format_port_usages(open_ports)
            await openport.finish(MessageSegment.reply(event.message_id) + f"检测结果 ({target}):\n开放端口：{open_ports_str}\n已知用途：\n{usages}\n(结果仅供参考，扫描器可能会被拦截或被欺骗)")
        else:
            await openport.finish(MessageSegment.reply(event.message_id) + f"检测结果 ({target}):\n没有发现开放的端口")

    finally:
        scan_in_progress = False

async def resolve_domain(host: str) -> str:
    try:
        addr_info = await asyncio.get_event_loop().getaddrinfo(host, None)
        for addr in addr_info:
            if addr[0] == socket.AF_INET6:
                return addr[4][0]
        for addr in addr_info:
            if addr[0] == socket.AF_INET:
                return addr[4][0]
    except socket.gaierror:
        return None

async def check_port_range(ip: str, start_port: int, end_port: int) -> dict:
    results = {}
    total_ports = end_port - start_port + 1
    chunk_size = 1000  # 每次并发扫描的端口数

    for chunk_start in range(start_port, end_port + 1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, end_port)
        tasks = [check_port(ip, port) for port in range(chunk_start, chunk_end + 1)]
        chunk_results = await asyncio.gather(*tasks)
        
        for port, is_open in zip(range(chunk_start, chunk_end + 1), chunk_results):
            results[port] = is_open
            if is_open:
                nonebot.logger.info(f"发现开放端口: {port}")

        progress = ((chunk_end - start_port + 1) / total_ports) * 100
        nonebot.logger.info(f"扫描进度: {progress:.2f}% (当前端口: {chunk_end})")

    nonebot.logger.info("端口扫描完成")
    return results

async def check_known_ports(ip: str) -> dict:
    tasks = [check_port(ip, port) for port in PORT_USAGE.keys()]
    results = await asyncio.gather(*tasks)
    return dict(zip(PORT_USAGE.keys(), results))

async def check_port(ip: str, port: int) -> bool:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=TIMEOUT)
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False

def format_port_ranges(ports):
    ranges = []
    start = end = ports[0]
    for port in ports[1:] + [None]:
        if port != end + 1:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = port
        end = port
    return ", ".join(ranges)

def format_port_usages(ports):
    usages = []
    for port in ports:
        if port in PORT_USAGE:
            usages.append(f"{port}: {PORT_USAGE[port]}")
    return "\n".join(usages)
