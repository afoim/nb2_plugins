from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException
from nonebot.adapters.onebot.v11 import MessageEvent
import time
import json
import os

plugin_dir = os.path.dirname(__file__)
json_file = os.path.join( 'data', 'sleep_time.json')
os.makedirs(os.path.dirname(json_file), exist_ok=True)

user_sleep_time = {}

def save_sleep_time():
    with open(json_file, 'w') as f:
        json.dump(user_sleep_time, f)

def load_sleep_time():
    global user_sleep_time
    try:
        with open(json_file, 'r') as f:
            user_sleep_time = json.load(f)
    except FileNotFoundError:
        user_sleep_time = {}

load_sleep_time()

@event_preprocessor
async def preprocess_sleep_time(bot: Bot, event: Event):
        # 只处理消息事件
    if not isinstance(event, MessageEvent):
        return
    
    user_id = str(event.user_id)
    message = str(event.message).strip()
    if message in ["晚安", "早安"]:
        try:
            await handle_sleep_time(bot, event, user_id, message)
        except Exception as e:
            await bot.send(event, f"处理睡眠时间时出错：{str(e)}")
        finally:
            raise IgnoredException("睡眠时间命令已处理")

async def handle_sleep_time(bot: Bot, event: Event, user_id: str, message: str):
    if message == "晚安":
        user_sleep_time[user_id] = time.time()
        save_sleep_time()
        reply = "晚安喵~( ´ ▿ ` )~"
    elif message == "早安":
        if user_id not in user_sleep_time:
            reply = "请先发送晚安，再发送早安哦(*￣▽￣)b~"
        else:
            time_diff = time.time() - user_sleep_time[user_id]
            hours, remainder = divmod(time_diff, 3600)
            minutes, seconds = divmod(remainder, 60)
            reply = f"你睡了(◎ ◎)ゞ：{int(hours)}小时{int(minutes)}分钟{int(seconds)}秒~"
    await bot.send(event, reply)