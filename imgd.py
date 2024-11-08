from nonebot import on_command, on_message, logger
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.permission import SUPERUSER
import os
import httpx
from datetime import datetime

# 全局变量
DOWNLOADER_STATE = {
    "running": False
}

# 确保下载目录存在
if not os.path.exists("img"):
    os.makedirs("img")
    logger.info("Created img directory")

# 命令处理器
start_cmd = on_command("imgd start", permission=SUPERUSER, priority=1, block=True)
stop_cmd = on_command("imgd down", permission=SUPERUSER, priority=1, block=True)

@start_cmd.handle()
async def handle_start(bot: Bot, event: MessageEvent):
    logger.info(f"Received start command from {event.get_user_id()}")
    if DOWNLOADER_STATE["running"]:
        await start_cmd.finish("图片下载器已经在运行中！")
    else:
        DOWNLOADER_STATE["running"] = True
        logger.info("Image downloader started")
        await bot.send_private_msg(user_id=event.user_id, message="图片下载器已启动！")

@stop_cmd.handle()
async def handle_stop(bot: Bot, event: MessageEvent):
    logger.info(f"Received stop command from {event.get_user_id()}")
    if not DOWNLOADER_STATE["running"]:
        await stop_cmd.finish("图片下载器已经是关闭状态！")
    else:
        DOWNLOADER_STATE["running"] = False
        logger.info("Image downloader stopped")
        await bot.send_private_msg(user_id=event.user_id, message="图片下载器已关闭！")

# 消息处理器
msg_handler = on_message(priority=5, block=False)

@msg_handler.handle()
async def handle_message(bot: Bot, event: MessageEvent):
    if not DOWNLOADER_STATE["running"]:
        return

    logger.info(f"Processing message from {event.get_user_id()}")
    message = event.get_message()
    
    # 处理消息中的每个段落
    for seg in message:
        if seg.type == "image":
            url = seg.data.get("url", "")
            if not url:
                continue
                
            logger.info(f"Found image URL: {url}")
            
            try:
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{hash(url) % 10000}.jpg"
                filepath = os.path.join("img", filename)
                
                # 下载图片
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                        logger.info(f"Successfully saved image: {filename}")
                        await bot.send_private_msg(
                            user_id=event.user_id,
                            message=f"图片已保存: {filename}"
                        )
                    else:
                        error_msg = f"下载失败: HTTP {response.status_code}"
                        logger.error(error_msg)
                        await bot.send_private_msg(
                            user_id=event.user_id,
                            message=error_msg
                        )
            
            except Exception as e:
                error_msg = f"下载出错: {str(e)}"
                logger.error(error_msg)
                await bot.send_private_msg(
                    user_id=event.user_id,
                    message=error_msg
                )

# 启动时的日志
logger.info("Image downloader plugin loaded")