import time
import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.typing import T_State

# 定义命令 "/URL测试"
test_url = on_command("URL测试", aliases={"/test_url"})

# URL 分类字典
url_categories = {
    "Cloudflare": ["https://pic.onani.cn"],  # 示例，替换为实际 Cloudflare URL
    "Github": ["https://github.com"],
    "CN Bing": ["https://cn.bing.com"],
    "Docker安装脚本": ["https://get.docker.com"],
    "Docker Hub": ["https://hub.docker.com"],
    "Google": ["https://www.google.com"],
    "Youtube": ["https://www.youtube.com"],
}

# 全局变量标记任务状态
task_running = False
start_time = None

@test_url.handle()
async def handle_first_receive(bot: Bot, event: Event, state: T_State):
    global task_running, start_time

    if task_running:
        elapsed_time = time.time() - start_time
        await test_url.send(f"已有一个 URL 测试任务正在运行。触发时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} | 已运行 {elapsed_time:.2f} 秒")
        return

    # 标记任务开始
    task_running = True
    start_time = time.time()
    start_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

    # 发送开始测试的消息
    await test_url.send("开始进行 URL 测试...")

    results = {}
    error_categories = []

    for category, urls in url_categories.items():
        for url in urls:
            url_start_time = time.time()  # 记录每个URL的开始时间
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    results[category] = f"{response.status_code} {response.reason_phrase}"
            except Exception:
                error_categories.append(category)

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
    )

    for category, status in results.items():
        result_message += f"{category} -> {status}\n"

    # 输出错误分类
    for category in error_categories:
        result_message += f"{category} -> Error\n"

    await test_url.send(result_message)

    # 标记任务结束
    task_running = False
    start_time = None
