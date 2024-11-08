import subprocess
import asyncio
import re
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event
import ipaddress

# 创建命令处理器，添加别名
masscan_cmd = on_command("masscan", aliases={"/masscan", "/openportscan"})

# 用于存储扫描进程
scan_process = None

# 正则表达式用于判断 IP 地址
ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")

# 检查是否为内网 IP 地址
def is_private_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False

# 处理 /masscan 命令
@masscan_cmd.handle()
async def handle_masscan(bot: Bot, event: Event):
    global scan_process

    # 获取命令参数
    args = str(event.get_message()).strip().split()
    
    if len(args) < 2:
        await masscan_cmd.finish("请提供扫描参数，如：`/masscan -p0-65535 61.241.148.225`。")
    
    # 如果命令是 -quit，尝试终止扫描进程
    if args[1].lower() == "-quit":
        if scan_process:
            scan_process.terminate()
            scan_process = None
            await masscan_cmd.send("扫描已被终止。")
        else:
            await masscan_cmd.finish("没有进行中的扫描进程。")
        return
    
    # 提取扫描命令和目标
    command = args[1]
    target = args[2]

    # 验证目标是否为 IP 地址
    if not ip_pattern.match(target):
        await masscan_cmd.finish("只允许对单个 IP 地址进行扫描，如果想要支持更多参数请自行在自己的设备上安装并运行masscan")

    # 检查目标是否为内网地址
    if is_private_ip(target):
        await masscan_cmd.finish("禁止内网渗透！")

    # 处理 --rate 参数，禁止更改为其他值，硬编码为 10000
    command_list = command.split()
    if '--rate' in command_list:
        await masscan_cmd.finish("`--rate` 参数不可更改，默认为 10000。")
    
    # 将 --rate 参数硬编码为 10000
    command_list.append('--rate')
    command_list.append('10000')

    # 检查是否已有扫描进程在运行
    if scan_process:
        await masscan_cmd.finish("已有扫描进程正在运行，请先停止当前扫描。")

    # 启动 masscan 扫描
    await masscan_cmd.send(f"开始扫描 {target}...终止请发：/masscan -quit")

    process = subprocess.Popen(
        ["masscan"] + command_list + [target],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    scan_process = process
    result = ""  # 初始化 result 变量

    try:
        # 使用 asyncio 来异步执行并支持超时
        stdout, stderr = await asyncio.wait_for(
            asyncio.to_thread(process.communicate),  # 将同步调用放入协程中运行
            timeout=60  # 设置超时时间为 60 秒
        )
        result = stdout if process.returncode == 0 else stderr

    except asyncio.TimeoutError:
        process.terminate()
        result = "扫描超时，进程已被终止。"

    finally:
        scan_process = None
        await masscan_cmd.send(f"扫描结果：\n{result}")
