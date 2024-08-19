from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
import psutil
import platform
import time
import nonebot
import subprocess
import socket
import os
import distro
from datetime import datetime

# 创建全局计数器
message_counter = 0

# 创建命令处理器
info_command = on_command("/status", priority=5)

# 创建消息处理器来计数所有消息
message_counter_handler = on_message(priority=10, block=False)

@message_counter_handler.handle()
async def count_message(bot: Bot, event: MessageEvent):
    global message_counter
    message_counter += 1

@info_command.handle()
async def handle_info(bot: Bot, event: MessageEvent):
    global message_counter
    
    # 获取Bot的信息
    bot_info = await bot.get_login_info()
    
    # 获取好友和群聊数量
    friend_list = await bot.get_friend_list()
    group_list = await bot.get_group_list()
    friend_count = len(friend_list)
    group_count = len(group_list)
    
    # 获取系统信息
    system_info = get_system_info()
    system_info["Bot账号"] = f"QQ {bot_info['user_id']}"
    system_info["好友"] = f"{friend_count}个"
    system_info["群聊"] = f"{group_count}个"

    
    # 生成纯文本信息
    text_content = generate_text(system_info)
    
    # 发送文本消息，引用原始消息
    reply_message = MessageSegment.reply(event.message_id) + MessageSegment.text(text_content)
    await bot.send(event, reply_message)

def get_cpu_info():
    try:
        output = subprocess.check_output("lscpu | grep 'Model name'", shell=True).decode().strip()
        return output.split(":")[1].strip()
    except:
        return "无法获取CPU信息"

def get_ip_addresses():
    ip_addresses = []
    hostname = socket.gethostname()
    try:
        ip_addresses = [ip for ip in socket.gethostbyname_ex(hostname)[2] if not ip.startswith('127.')]
    except socket.error:
        pass
    return ', '.join(ip_addresses) if ip_addresses else "无IP地址"

def get_network_info():
    net_info = psutil.net_if_addrs()
    net_status = psutil.net_if_stats()
    net_io = psutil.net_io_counters(pernic=True)
    info = []
    for interface, addrs in net_info.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                info.append(f"{interface} (IPv4): {addr.address}")
            elif addr.family == socket.AF_INET6:
                info.append(f"{interface} (IPv6): {addr.address}")
            elif addr.family == psutil.AF_LINK:
                info.append(f"{interface} (MAC): {addr.address}")
        if interface in net_status:
            info.append(f"{interface} 状态: {'up' if net_status[interface].isup else 'down'}, 速度: {net_status[interface].speed} Mbps")
        if interface in net_io:
            io = net_io[interface]
            info.append(f"{interface} 流量: 接收 {io.bytes_recv / (1024**2):.2f} MB, 发送 {io.bytes_sent / (1024**2):.2f} MB")
    return info

def get_disk_info():
    partitions = psutil.disk_partitions()
    info = []
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        info.append(f"{partition.device} ({partition.mountpoint}): {usage.percent}% 使用 ({usage.used / (1024**3):.2f} GB/{usage.total / (1024**3):.2f} GB, 文件系统: {partition.fstype})")
    return info

def get_top_processes():
    processes = [(p.info['cpu_percent'], p.info['name']) for p in psutil.process_iter(attrs=['name', 'cpu_percent']) if p.info['cpu_percent'] > 0]
    processes.sort(reverse=True)
    return ", ".join([f"{name} ({cpu}%)" for cpu, name in processes[:5]]) if processes else "无数据"

def get_gpu_info():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_info = []
            for gpu in gpus:
                gpu_info.append(f"{gpu.name}: {gpu.load * 100:.2f}% 使用 ({gpu.memoryUsed / 1024:.2f} GB/{gpu.memoryTotal / 1024:.2f} GB)")
            return ", ".join(gpu_info)
        return "无GPU信息"
    except ImportError:
        return "GPUtil模块未安装"

def get_system_info():
    info = {}

    # 系统信息
    info["系统版本"] = platform.system() + " " + platform.version()
    info["系统架构"] = platform.architecture()[0]
    info["内核版本"] = platform.release()
    info["UEFI或BIOS启动"] = "UEFI" if os.path.exists('/sys/firmware/efi') else "BIOS"

    # NoneBot2 信息
    info["NoneBot2版本"] = nonebot.__version__
    info["Bot连接协议"] = "OneBot v11"
    info["Bot协议实现"] = "Lagrange.OneBot"

    # Python 信息
    info["Python版本"] = platform.python_version()

    # 系统运行时间
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    info["系统启动时间"] = boot_time
    info["系统运行时间"] = str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))

    # Bot 启动时间
    info["本次Bot启动时间"] = str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))  # 需要实际获取Bot启动时间的方法

    # CPU 信息
    cpu_info = psutil.cpu_freq()
    cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
    info["CPU型号"] = get_cpu_info()
    info["CPU频率"] = f"{cpu_info.current:.2f} MHz"
    info["CPU总占用率"] = f"{sum(cpu_usage) / len(cpu_usage):.1f}%"
    info["CPU各核心占用率"] = ", ".join(f"{x:.1f}%" for x in cpu_usage)

    # 内存信息
    mem = psutil.virtual_memory()
    info["内存使用"] = f"{mem.percent:.1f}% ({mem.used / (1024 ** 3):.2f} GB / {mem.total / (1024 ** 3):.2f} GB)"

    # 存储信息
    disk = psutil.disk_usage('/')
    info["存储使用"] = f"{disk.percent:.1f}% ({disk.used / (1024 ** 3):.2f} GB / {disk.total / (1024 ** 3):.2f} GB)"

    # 平均负载
    load_avg = os.getloadavg()
    info["平均负载"] = f"{load_avg[0]:.2f} (1分钟), {load_avg[1]:.2f} (5分钟), {load_avg[2]:.2f} (15分钟)"

    # 当前登录用户
    users = psutil.users()
    ssh_users = [f"{user.name}@{user.host}" for user in users if user.host]
    info["当前登录用户"] = ", ".join(ssh_users) if ssh_users else "无用户"

    # 电池状态
    battery = psutil.sensors_battery()
    info["电池状态"] = "插电" if battery is None else ("充电" if battery.power_plugged else "电池" if battery.percent < 100 else "已充满")

    return info

def generate_text(data):
    text_content = "\n".join([f"{key}: {value}" for key, value in data.items()])
    return text_content