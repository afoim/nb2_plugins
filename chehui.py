import json
import os
from pathlib import Path
from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, Message
from nonebot.typing import T_State
import nonebot
import jieba
from pypinyin import lazy_pinyin, Style

def text_to_pinyin(text: str) -> str:
    """将文本转换为拼音，并返回不带声调的小写形式"""
    return ' '.join(lazy_pinyin(text, style=Style.NORMAL))

# 读取配置文件
try:
    config_path = Path(__file__).parent / "chehui" / "chehui.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    ALLOWED_GROUPS = config.get("allowed_groups", [])
    RULES = config.get("rules", [])
except Exception as e:
    nonebot.logger.error(f"读取配置文件失败: {e}")
    ALLOWED_GROUPS = []
    RULES = []

# 创建消息匹配器
nzl = on_message(priority=1, block=False)

@nzl.handle()
async def handle_nzl(bot: Bot, event: GroupMessageEvent, state: T_State):
    # nonebot.logger.info(f"收到群 {event.group_id} 的消息: {event.message.extract_plain_text()}")
    
    if event.group_id not in ALLOWED_GROUPS:
        # nonebot.logger.info(f"群 {event.group_id} 不在允许列表中")
        await nzl.finish()
    
    msg_text = event.message.extract_plain_text()
    msg_pinyin = text_to_pinyin(msg_text)  # 将消息转换为拼音
    
    for rule in RULES:
        trigger_pinyin = text_to_pinyin(rule["trigger"])  # 将规则的触发词转换为拼音
        if msg_text == rule["trigger"] or msg_pinyin == trigger_pinyin:
            # nonebot.logger.info(f"触发了{rule['trigger']}检测，准备执行操作")
            # 撤回消息
            await bot.delete_msg(message_id=event.message_id)
            
            # 禁言用户
            ban_time = rule["ban_time"]
            await bot.set_group_ban(
                group_id=event.group_id,
                user_id=event.user_id,
                duration=ban_time
            )
            
            # 发送提示消息
            reply = Message(f"[CQ:at,qq={event.user_id}] {rule['reply_message'].format(ban_time=ban_time)}")
            await nzl.finish(reply)
