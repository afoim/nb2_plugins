import nonebot
from nonebot import on_command
from nonebot.adapters import Bot, Event
import asyncio
import psutil
import time

netmon = on_command("netmon", aliases={"网络监控"}, priority=5)

@netmon.handle()
async def handle_netmon(bot: Bot, event: Event):
    # 获取初始网络统计信息
    net_io_counters_start = psutil.net_io_counters()
    time_start = time.time()
    
    # 等待5秒
    await asyncio.sleep(5)
    
    # 获取结束时的网络统计信息
    net_io_counters_end = psutil.net_io_counters()
    time_end = time.time()
    
    # 计算网络速度
    bytes_sent = net_io_counters_end.bytes_sent - net_io_counters_start.bytes_sent
    bytes_recv = net_io_counters_end.bytes_recv - net_io_counters_start.bytes_recv
    time_elapsed = time_end - time_start
    
    send_speed = bytes_sent / time_elapsed / 1024  # KB/s
    recv_speed = bytes_recv / time_elapsed / 1024  # KB/s
    
    # 发送结果
    await netmon.finish(f"当前网络速度:\n"
                        f"上传: {send_speed:.2f} KB/s\n"
                        f"下载: {recv_speed:.2f} KB/s")