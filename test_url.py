import time
import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.typing import T_State

# 定义命令 "/test_url"
test_url = on_command("test_url", aliases={"/test_url"})

# 硬编码的URL列表
URLS = [
    "https://www.google.com",
    "https://github.com",
    "https://www.baidu.com",
    "https://cn.bing.com/",
    "https://hrandom.onani.cn",
    "https://vrandom.onani.cn",
    "https://acofork.cn",
    "https://alist.onani.cn"
]

# 全局变量标记任务状态
task_running = False
start_time = None

@test_url.handle()
async def handle_first_receive(bot: Bot, event: Event, state: T_State):
    global task_running, start_time

    if task_running:
        elapsed_time = time.time() - start_time
        await test_url.send(f"已有一个test_url任务正在运行。触发时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} | 已经运行了 {elapsed_time:.2f}秒")
        return

    # 标记任务开始
    task_running = True
    start_time = time.time()

    results = []
    
    for url in URLS:
        url_start_time = time.time()  # 记录每个URL的开始时间
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                load_time = time.time() - url_start_time  # 计算加载时间
                results.append(f"URL: {url} | Status Code: {response.status_code} | Load Time: {load_time:.2f} seconds")
        except Exception as e:
            results.append(f"URL: {url} | Error: {str(e)}")

    # 将结果拼接成一个字符串发送
    result_message = "\n".join(results)
    await test_url.send(result_message)

    # 标记任务结束
    task_running = False
    start_time = None
