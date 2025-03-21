from nonebot import on_command
from nonebot.adapters import Bot, Event
import asyncio
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
        # 使用异步子进程运行 ping 命令
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 异步等待命令执行完成并获取输出
        stdout_bytes, stderr_bytes = await process.communicate()
        
        # 将字节输出转换为字符串
        stdout = stdout_bytes.decode('utf-8')
        stderr = stderr_bytes.decode('utf-8')
        
        if process.returncode == 0:
            await ping.send(stdout.strip())
        else:
            await ping.send(f"Ping 操作失败: {stderr.strip()}")
    except Exception as e:
        await ping.send(f"发生错误: {str(e)}")