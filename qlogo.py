import base64
import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment

# 创建命令触发器
qlogo = on_command("qlogo", priority=5)

@qlogo.handle()
async def handle_qlogo(bot: Bot, event: Event):
    # 获取命令参数并打印调试信息
    args = str(event.get_message()).strip().split()
    # print(f"命令参数: {args}")  # 打印命令参数

    # 如果没有参数，使用发送者的QQ号
    if len(args) <= 1:  # 如果只有命令部分，没有其他参数
        qq = str(event.get_user_id())  # 使用发送者的QQ号
    else:
        # 如果有参数，使用第二个参数作为QQ号
        qq = args[1]

    # print(f"使用的QQ号: {qq}")  # 打印解析出来的QQ号
    
    try:
        # 构建QQ头像的URL
        avatar_url = f"https://q2.qlogo.cn/headimg_dl?dst_uin={qq}&spec=5"
        
        # 异步获取头像图片
        async with httpx.AsyncClient() as client:
            response = await client.get(avatar_url)
            
            # # 输出状态码和响应内容以便调试
            # print(f"请求头像URL: {avatar_url}")
            # print(f"响应状态码: {response.status_code}")
            if response.status_code == 200:
                # 将图片转换为base64编码
                image_base64 = base64.b64encode(response.content).decode()
                
                # 构造消息，同时发送URL和图片
                await qlogo.finish(
                    MessageSegment.text(avatar_url) + 
                    MessageSegment.image(f"base64://{image_base64}")
                )
            else:
                # 打印详细的错误信息
                await qlogo.finish(f"获取头像失败，HTTP状态码: {response.status_code}")
    
    except Exception as e:
        # await qlogo.finish(f"发生错误：{str(e)}")
        return
