from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import subprocess
import asyncio

openport = on_command("/openport", priority=5)
stop_openport = on_command("/openport stop", priority=5)

# 用于跟踪扫描任务的状态
scan_in_progress = False
scan_process = None

@openport.handle()
async def handle_openport(bot: Bot, event: Event, args: Message = CommandArg()):
    global scan_in_progress, scan_process
    
    if scan_in_progress:
        await openport.finish(MessageSegment.reply(event.message_id) + "已有扫描任务正在进行中，请稍后再试。")
    
    arg_list = args.extract_plain_text().strip().split()
    if len(arg_list) < 1:
        await openport.finish(MessageSegment.reply(event.message_id) + "请提供要测试的IP地址或域名")
    
    target = arg_list[0]
    
    scan_in_progress = True
    try:
        await openport.send(MessageSegment.reply(event.message_id) + f"开始扫描 {target}，这可能需要一些时间...\n发送 /openport stop 以终止本次扫描")
        
        results = await run_nmap_scan(target)
        
        if scan_in_progress:  # 只有在扫描没有被停止的情况下才发送结果
            if results:
                await openport.finish(MessageSegment.reply(event.message_id) + f"检测结果 ({target}):\n{results}")
            else:
                await openport.finish(MessageSegment.reply(event.message_id) + f"检测结果 ({target}):\n没有发现开放的端口")

    finally:
        scan_in_progress = False

async def run_nmap_scan(target: str) -> str:
    global scan_process
    
    cmd = ['nmap', target]
    
    try:
        scan_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        output = []
        while True:
            line = await scan_process.stdout.readline()
            if not line and scan_process.returncode is not None:
                break
            output.append(line.decode('gbk', errors='ignore').strip())

            # 检查扫描状态，若被停止则直接返回
            if not scan_in_progress:
                scan_process.kill()  # 杀死进程
                return ""

        return "\n".join(output)

    except Exception:
        # 在这里不返回具体的错误信息，以避免发送到用户
        return ""

@stop_openport.handle()
async def handle_stop_openport(bot: Bot, event: Event):
    global scan_in_progress, scan_process
    
    if not scan_in_progress:
        await stop_openport.finish(MessageSegment.reply(event.message_id) + "没有正在进行的扫描任务。")
    
    # 直接杀死扫描任务
    if scan_process:
        scan_process.kill()
        scan_process = None
    
    scan_in_progress = False
    await stop_openport.finish(MessageSegment.reply(event.message_id) + "扫描任务已终止。")
