from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
import psutil
import platform
import subprocess
from datetime import datetime
import nonebot
import distro  # 新增导入

# 创建全局计数器和启动时间
message_counter = 0
bot_start_time = datetime.now()

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
    
    # 获取连接协议
    system_info["Bot连接协议"] = bot.adapter.get_name()  # 获取适配器名称

    # 生成纯文本信息
    text_content = generate_text(system_info)
    
    # 确保 reply_message 有效
    reply_message = MessageSegment.text(text_content)
    if event.message_id:  # 确保有有效的消息 ID
        reply_message = MessageSegment.reply(event.message_id) + reply_message
    
    await bot.send(event, reply_message)


def get_cpu_info():
    try:
        output = subprocess.check_output("lscpu", shell=True).decode().strip()
        cpu_model = None
        for line in output.split("\n"):
            if "Model name" in line:
                cpu_model = line.split(":")[1].strip()
                break
        # 获取核数和线程数
        cpu_cores = psutil.cpu_count(logical=False)  # 物理核心数
        cpu_threads = psutil.cpu_count(logical=True)  # 逻辑核心数
        return f"{cpu_model} ({cpu_cores}核 {cpu_threads}线程)"
    except Exception:
        return "无法获取CPU信息"

def get_gpu_info():
    try:
        output = subprocess.check_output("lspci | grep -i vga", shell=True).decode().strip()
        gpus = output.split("\n")
        gpu_info_list = []
        for gpu in gpus:
            if gpu.strip():  # 如果当前行有内容
                # 提取型号部分
                model = gpu.split(":")[2].strip() if len(gpu.split(":")) > 2 else gpu
                gpu_info_list.append({"型号": model})
        return gpu_info_list
    except Exception as e:
        return f"无法获取GPU信息，错误: {str(e)}"

def get_system_info():
    info = {}
    
    # 系统信息
    system_version = platform.system() + " " + platform.version()
    info["发行版"] = distro.name() + " " + distro.version()  # 获取发行版信息
    info["系统版本"] = system_version
    info["系统架构"] = platform.architecture()[0]
    info["内核版本"] = platform.release()  # 这里是内核版本

    # NoneBot2 信息
    info["NoneBot2版本"] = nonebot.__version__

    # Python 信息
    info["Python版本"] = platform.python_version()

    # 系统运行时间
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    info["系统启动时间"] = boot_time
    info["系统运行时间"] = str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))

    # Bot 启动时间
    info["本次Bot启动时间"] = str(datetime.now() - bot_start_time)

    # CPU 信息
    cpu_info = psutil.cpu_freq()
    cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
    info["CPU型号"] = get_cpu_info()
    info["CPU频率"] = f"{cpu_info.current:.2f} MHz"
    info["CPU总占用率"] = f"{sum(cpu_usage) / len(cpu_usage):.1f}%"
    info["CPU各核心占用率"] = ", ".join(f"{x:.1f}%" for x in cpu_usage)

    # GPU 信息
    gpu_info = get_gpu_info()
    info["GPU信息"] = gpu_info

    # 内存信息
    mem = psutil.virtual_memory()
    info["内存使用"] = f"{mem.percent:.1f}% ({mem.used / (1024 ** 3):.2f} GB / {mem.total / (1024 ** 3):.2f} GB)"

    # 存储信息
    disk = psutil.disk_usage('/')
    info["存储使用"] = f"{disk.percent:.1f}% ({disk.used / (1024 ** 3):.2f} GB / {disk.total / (1024 ** 3):.2f} GB)"

    # 网络流量信息
    net_io = psutil.net_io_counters()
    info["总接收"] = f"{net_io.bytes_recv / (1024 ** 2):.2f} MB"
    info["总发送"] = f"{net_io.bytes_sent / (1024 ** 3):.2f} GB"

    # 当前登录用户
    users = psutil.users()
    ssh_users = [f"{user.name}@{user.host}" for user in users if user.host]
    info["当前登录用户"] = ", ".join(ssh_users) if ssh_users else "无用户"

    # 电池状态
    battery = psutil.sensors_battery()
    info["电池状态"] = "插电" if battery is None else ("充电" if battery.power_plugged else "电池" if battery.percent < 100 else "已充满")

    return info

def generate_text(data):
    text_content = f"""AcoFork的
NoneBot {data['NoneBot2版本']}
协议：{data['Bot连接协议']}
Python {data['Python版本']}
{data['Bot账号']}

发行版：{data['发行版']}
系统：{data['系统版本']}
内核：{data['内核版本']}
架构：{data['系统架构']}
初次启动：{data['系统启动时间']}
已运行 {str(data['系统运行时间']).split('.')[0]}
用户：{data['当前登录用户']}
电源状态：{data['电池状态']}
本次Bot运行 {str(data['本次Bot启动时间']).split('.')[0]}

CPU：
型号：{data['CPU型号']}
频率：{data['CPU频率']}
总占用：{data['CPU总占用率']}
各核心占用：{data['CPU各核心占用率']}

GPU：
"""
    for gpu in data["GPU信息"]:
        text_content += f"型号：{gpu['型号']}\n"
    text_content += f"""
内存：
使用量：{data['内存使用']}

存储：
总使用率：{data['存储使用']}

网络：
总接收：{data['总接收']}
总发送：{data['总发送']}

打印时间：{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
"""
    return text_content.strip()
