from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.permission import SUPERUSER
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException

# 定义超级用户的QQ号
SUPERUSER_ID = 2973517380

# 定义管理命令
admin_commands = ["禁言", "踢人", "解除禁言"]

# 消息预处理器
@event_preprocessor
async def preprocess_admin_commands(bot: Bot, event: GroupMessageEvent):
    if isinstance(event, GroupMessageEvent):
        message = event.get_message()
        if message and message[0].type == "text":
            command = message[0].data["text"].strip()
            if any(command.startswith(cmd) for cmd in admin_commands):
                if event.user_id == SUPERUSER_ID:
                    try:
                        await handle_admin_command(bot, event)
                    except Exception as e:
                        await bot.send(event, f"处理命令时出错：{str(e)}")
                    finally:
                        raise IgnoredException("管理命令已处理")
                else:
                    raise IgnoredException("非管理员尝试执行管理命令")

async def handle_admin_command(bot: Bot, event: GroupMessageEvent):
    message = event.get_message()
    group_id = event.group_id

    if message[0].type == "text" and message[0].data["text"].startswith("禁言"):
        if len(message) >= 3 and message[1].type == "at" and message[2].type == "text":
            user_id = int(message[1].data["qq"])
            duration = int(message[2].data["text"].strip())
            
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=duration)
            await bot.send(event, f"已经让 {user_id} 闭嘴 {duration}秒了喵~")
            print(f"已禁言用户 {user_id} {duration}秒")  # 调试信息

    elif message[0].type == "text" and message[0].data["text"].startswith("踢人"):
        if len(message) >= 2 and message[1].type == "at":
            user_id = int(message[1].data["qq"])
            
            await bot.set_group_kick(group_id=group_id, user_id=user_id)
            await bot.send(event, f"含泪踢出 {user_id} 喵~")
            print(f"已踢出用户 {user_id}")  # 调试信息

    elif message[0].type == "text" and message[0].data["text"].startswith("解除禁言"):
        print("开始处理解除禁言命令")  # 调试信息
        if len(message) >= 2 and message[1].type == "at":
            user_id = int(message[1].data["qq"])
            print(f"解除禁言用户 {user_id}")  # 调试信息
            
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=0)
            await bot.send(event, f"喵喵？你可以说话了喵~： {user_id}")
            print(f"已解除禁言用户 {user_id}")  # 调试信息

# 移除原有的消息处理器，因为我们现在使用预处理器来处理这些命令
# message_handler = on_message(permission=SUPERUSER)
# @message_handler.handle()
# async def handle_message(bot: Bot, event: GroupMessageEvent):
#     ...  # 原有的处理逻辑移到了 handle_admin_command 函数中