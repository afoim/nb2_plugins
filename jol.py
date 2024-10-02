import json
import os
from pathlib import Path
from datetime import datetime
from nonebot import on_notice, on_command, get_driver
from nonebot.adapters.onebot.v11 import GroupIncreaseNoticeEvent, GroupDecreaseNoticeEvent, Bot
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Message

__plugin_meta__ = PluginMetadata(
    name="群通知插件",
    description="处理加群和退群通知，显示用户名字",
    usage="管理员可以使用 /(开启|关闭)(加群|退群)通知 来控制功能，使用 /群通知状态 查看状态，使用 /默认(开启|关闭)(加群|退群)通知 设置默认状态"
)

# 获取数据目录
try:
    data_dir = get_driver().config.data_dir
except AttributeError:
    data_dir = Path.home() / ".nonebot" / "group_notice_plugin"

# 确保数据目录存在
os.makedirs(data_dir, exist_ok=True)

config_file = os.path.join(data_dir, "group_notice_config.json")

def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return {"group_status": {}, "default_status": {"increase": False, "decrease": True}}

def save_config(config):
    with open(config_file, "w") as f:
        json.dump(config, f)

config = load_config()

group_increase = on_notice()
group_decrease = on_notice()

@group_increase.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = str(event.group_id)
    if config["group_status"].get(group_id, {}).get("increase", config["default_status"]["increase"]):
        user_id = event.user_id
        user_info = await bot.get_group_member_info(group_id=event.group_id, user_id=user_id)
        user_name = user_info['card'] if user_info['card'] else user_info['nickname']
        await group_increase.finish(f"欢迎新成员 {user_name}-QQ {user_id} 加入群！")

@group_decrease.handle()
async def handle_group_decrease(bot: Bot, event: GroupDecreaseNoticeEvent):
    group_id = str(event.group_id)
    if config["group_status"].get(group_id, {}).get("decrease", config["default_status"]["decrease"]):
        user_id = event.user_id
        user_info = await bot.get_stranger_info(user_id=user_id)
        user_name = user_info['nickname']
        await group_decrease.finish(f"成员 {user_name}-QQ {user_id} 已离开群。")

status_notice = on_command("群通知状态", permission=SUPERUSER)

@status_notice.handle()
async def show_notice_status(bot: Bot, arg: Message = CommandArg()):
    arg_text = arg.extract_plain_text().strip()
    show_group_id = arg_text == "-a"
    
    mode = "危险" if show_group_id else "安全"
    status_msg = f"群通知状态控制面板（{mode}模式）\n"
    status_msg += f"默认群通知状态：加群：{'开启' if config['default_status']['increase'] else '关闭'}，退群：{'开启' if config['default_status']['decrease'] else '关闭'}\n\n"
    
    group_list = await bot.get_group_list()
    for group in group_list:
        group_id = str(group['group_id'])
        group_name = group['group_name']
        group_status = config['group_status'].get(group_id, {})
        increase_status = group_status.get('increase', config['default_status']['increase'])
        decrease_status = group_status.get('decrease', config['default_status']['decrease'])
        
        status_str = f"加群：{'开启' if increase_status else '关闭'}，退群：{'开启' if decrease_status else '关闭'}"
        if show_group_id:
            status_msg += f"{group_name}（{group_id}）：{status_str}\n"
        else:
            status_msg += f"{group_name}：{status_str}\n"
    
    status_msg += "\n管理员可以前往对应群聊发送(开启/关闭)(加群/退群)通知"
    
    await status_notice.finish(status_msg.strip())

toggle_notice = on_command("开启加群通知", aliases={"关闭加群通知", "开启退群通知", "关闭退群通知"}, permission=SUPERUSER)

@toggle_notice.handle()
async def toggle_group_notice(bot: Bot, state: T_State):
    global config
    cmd = state["_prefix"]["raw_command"]
    
    group_id = str(state.get("group_id", ""))
    if group_id not in config["group_status"]:
        config["group_status"][group_id] = {}
    
    if "开启加群通知" in cmd:
        config["group_status"][group_id]["increase"] = True
        message = "加群通知已开启"
    elif "关闭加群通知" in cmd:
        config["group_status"][group_id]["increase"] = False
        message = "加群通知已关闭"
    elif "开启退群通知" in cmd:
        config["group_status"][group_id]["decrease"] = True
        message = "退群通知已开启"
    elif "关闭退群通知" in cmd:
        config["group_status"][group_id]["decrease"] = False
        message = "退群通知已关闭"
    
    save_config(config)
    await toggle_notice.finish(message)

default_notice = on_command("默认开启加群通知", aliases={"默认关闭加群通知", "默认开启退群通知", "默认关闭退群通知"}, permission=SUPERUSER)

@default_notice.handle()
async def set_default_notice(state: T_State):
    global config
    cmd = state["_prefix"]["raw_command"]
    
    if "默认开启加群通知" in cmd:
        config["default_status"]["increase"] = True
        message = "默认加群通知已开启"
    elif "默认关闭加群通知" in cmd:
        config["default_status"]["increase"] = False
        message = "默认加群通知已关闭"
    elif "默认开启退群通知" in cmd:
        config["default_status"]["decrease"] = True
        message = "默认退群通知已开启"
    elif "默认关闭退群通知" in cmd:
        config["default_status"]["decrease"] = False
        message = "默认退群通知已关闭"
    
    save_config(config)
    await default_notice.finish(message)
