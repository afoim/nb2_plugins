from nonebot import on_command
from nonebot.adapters import Bot, Event
import subprocess

ping = on_command("ping", aliases={"ping"})

@ping.handle()
async def handle_ping(bot: Bot, event: Event):
    args = event.get_plaintext().strip().split()
    if len(args) < 2:
        await ping.send("请提供一个 IP 地址，例如: /ping 1.1.1.1")
        return
    
    ip_address = args[1]
    command = f"ping -c 4 {ip_address}"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        await ping.send(result.stdout if result.returncode == 0 else result.stderr)
    except Exception as e:
        await ping.send(f"发生错误: {str(e)}")
