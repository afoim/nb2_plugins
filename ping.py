from nonebot import on_command
from nonebot.adapters import Bot, Event
import subprocess
import platform

ping = on_command("ping", aliases={"ping"})

@ping.handle()
async def handle_ping(bot: Bot, event: Event):
    args = event.get_plaintext().strip().split()
    if len(args) < 2:
        await ping.send("请提供一个 IP 地址或域名，例如: /ping 1.1.1.1")
        return
    
    ip_address = args[1]
    # 根据操作系统选择适当的 ping 命令
    system = platform.system()
    if system == "Windows":
        command = f"ping -n 4 {ip_address}"  # Windows 使用 -n 指定次数
    else:
        command = f"ping -c 4 {ip_address}"  # Linux/macOS 使用 -c 指定次数

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            await ping.send(result.stdout.strip())
        else:
            await ping.send(f"Ping 操作失败: {result.stderr.strip()}")
    except Exception as e:
        await ping.send(f"发生错误: {str(e)}")
