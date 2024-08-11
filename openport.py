from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import subprocess
import asyncio

openport = on_command("/openport", priority=5)

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
    
    scan_in_progress = True
    try:
        await openport.send(MessageSegment.reply(event.message_id) + f"开始扫描 {target}，这可能需要一些时间...")
        
        results = await run_nmap_scan(target)
        
        if results:
            await openport.finish(MessageSegment.reply(event.message_id) + f"检测结果 ({target}):\n{results}")
        else:
            await openport.finish(MessageSegment.reply(event.message_id) + f"检测结果 ({target}):\n没有发现开放的端口")

    finally:
        scan_in_progress = False

async def run_nmap_scan(target: str) -> str:
    # 构建 nmap 命令
    cmd = ['nmap', target]
    
    # 执行 nmap 命令并获取输出
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stderr:
            return f"错误：{stderr.decode().strip()}"
        
        return stdout.decode().strip()
    except Exception as e:
        return f"执行 nmap 失败: {str(e)}"
