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
    "https://www.youtube.com",
    "https://github.com",
    "https://www.baidu.com",
    "https://cn.bing.com/",
    "https://pic.onani.cn",
    "https://afo.im",
]

# 全局变量标记任务状态
task_running = False
start_time = None

@test_url.handle()
async def handle_first_receive(bot: Bot, event: Event, state: T_State):
    global task_running, start_time

    if task_running:
        elapsed_time = time.time() - start_time
        await test_url.send(f"已有一个 test_url 任务正在运行。触发时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} | 已运行 {elapsed_time:.2f} 秒")
        return

    # 标记任务开始
    task_running = True
    start_time = time.time()
    start_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

    reachable_urls = []
    unreachable_urls = []
    
    for url in URLS:
        url_start_time = time.time()  # 记录每个URL的开始时间
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                load_time = time.time() - url_start_time  # 计算加载时间
                reachable_urls.append(f"{url} 状态码：{response.status_code}")
        except Exception:
            unreachable_urls.append(f"{url} 状态码：无")

    # 标记任务结束
    end_time = time.time()
    end_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    duration = end_time - start_time

    # 拼接结果
    result_message = (
        "URL测试完毕。\n"
        f"开始时间：{start_time_str}\n"
        f"结束时间：{end_time_str}\n"
        f"持续时间：{duration:.2f} 秒\n\n"
        "可达URL：\n"
    )
    result_message += "\n".join(reachable_urls) if reachable_urls else "无可达URL。\n"
    
    result_message += "\n\n不可达URL：\n"
    result_message += "\n".join(unreachable_urls) if unreachable_urls else "无不可达URL。"

    await test_url.send(result_message)

    # 标记任务结束
    task_running = False
    start_time = None
