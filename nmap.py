import subprocess
import asyncio
from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import Bot, Event

# 创建命令处理器，添加两个别名
nmap_cmd = on_command("nmap", aliases={"/nmap", "/openport"})

# 用于存储扫描进程
scan_process = None

# 处理 /nmap x.x.x.x 或 /nmap domain 命令
@nmap_cmd.handle()
async def handle_nmap(bot: Bot, event: Event):
    global scan_process

    # 获取命令参数
    args = str(event.get_message()).strip().split()
    if len(args) < 2:
        await nmap_cmd.finish("请提供 IP 地址或域名。")
    
    command = args[1]

    # 停止正在进行的扫描进程
    if command.lower() == "stop":
        if scan_process:
            scan_process.terminate()
            scan_process = None
            await nmap_cmd.send("停止扫描")
        else:
            await nmap_cmd.finish("没有进行中的扫描。")
        return

    if scan_process:
        await nmap_cmd.finish("已有扫描进程正在运行，请先停止当前扫描。")

    await nmap_cmd.send(f"开始扫描 {command}...")

    # 启动 nmap 扫描
    process = subprocess.Popen(
        ["nmap", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    scan_process = process
    result = ""  # 初始化 result 变量

    try:
        # 使用 asyncio.create_subprocess_shell 来支持协程中的命令调用，并设置超时
        stdout, stderr = await asyncio.wait_for(
            asyncio.to_thread(process.communicate),  # 将同步调用放入协程中运行
            timeout=60  # 设置超时时间为60秒
        )
        result = stdout if process.returncode == 0 else stderr

    except asyncio.TimeoutError:
        process.terminate()
        result = "扫描超时，进程已被终止。"

    finally:
        scan_process = None
        await nmap_cmd.send(f"扫描结果：\n{result}")

