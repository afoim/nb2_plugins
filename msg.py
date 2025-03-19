import nonebot
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.log import logger
from datetime import datetime
from nonebot.drivers import Driver

# 获取驱动器实例
driver = nonebot.get_driver()

# 添加详细日志记录
logger.add("forward_msg_debug.log", rotation="10 MB", level="DEBUG")

forward_msg = on_command("/msg")

@forward_msg.handle()
async def handle_forward_msg(bot: Bot, event: Event):
    try:
        # 记录完整的事件信息进行调试
        # logger.debug(f"收到事件类型: {type(event)}")
        # logger.debug(f"完整事件信息: {event.dict()}")
        
        # 记录原始消息
        raw_message = str(event.get_message())
        # logger.debug(f"原始消息内容: {raw_message}")
        
        # 详细的消息解析过程
        parts = raw_message.split(" ", 1)
        # logger.debug(f"消息分割结果: {parts}")
        
        # 检查消息是否有内容
        if len(parts) < 2 or not parts[1].strip():
            # logger.warning("消息为空")
            await forward_msg.finish("转发消息不能为空")
        
        # 提取消息内容
        msg_content = parts[1].strip()
        # logger.debug(f"提取的消息内容: {msg_content}")
        
        # 获取发送者信息
        if isinstance(event, GroupMessageEvent):
            sender_group = event.group_id
            
            # 直接获取群信息
            group = await bot.get_group_info(group_id=sender_group)
            sender_group_name = group['group_name']
            
            sender_nickname = event.sender.nickname
            # logger.debug(f"群消息 - 群号: {sender_group}, 群名: {sender_group_name}")
        else:
            sender_group = "私聊"
            sender_group_name = "私聊"
            sender_nickname = event.sender.nickname
            # logger.debug("私聊消息")
        
        # logger.debug(f"发送者昵称: {sender_nickname}")
        
        # 构建转发消息
        forward_content = (
            f"发送方：{sender_nickname}\n"
            f"发送群聊：{sender_group_name} ({sender_group})\n"
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"正文：{msg_content}"
        )
        
        # logger.debug(f"构建的转发消息:\n{forward_content}")
        
        try:
            # 获取超级用户列表
            superusers = list(driver.config.superusers)
            if not superusers:
                await forward_msg.finish("未配置超级用户，消息转发失败", reply_message=True)
                return
            
            # 转发给第一个超级用户
            await bot.send_private_msg(user_id=int(superusers[0]), message=forward_content)
            await forward_msg.finish("消息转发成功", reply_message=True)
        except Exception as forward_error:
            return
    
    except Exception as e:
        # logger.exception(f"处理消息时发生未捕获的异常: {e}")
        # await forward_msg.finish(f"处理消息时发生错误：{str(e)}")
        return