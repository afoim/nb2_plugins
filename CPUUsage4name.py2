import asyncio
import psutil
import nonebot
from nonebot import require, get_bot
from nonebot.adapters.onebot.v11 import Bot

scheduler = require("nonebot_plugin_apscheduler").scheduler

# 配置初始群名片，如果为 None 则使用机器人当前的群名片
INITIAL_CARD = "和泉妃爱"  # 您可以在这里设置初始群名片，或设为 None

# 用于存储原始群名片的字典
original_cards = {}

# 标记是否是第一次运行
first_run = True

@scheduler.scheduled_job("interval", seconds=10)
async def update_cpu_usage():
    global first_run
    
    if first_run:
        # 第一次运行时延迟5秒
        await asyncio.sleep(5)
        first_run = False
    
    # 获取整个系统的CPU使用率，精确到2位小数
    cpu_percent = round(psutil.cpu_percent(interval=None, percpu=False), 2)
    
    # 计算魔力值
    magic_value = int(cpu_percent * 10)
    
    # 格式化CPU使用率和魔力值前缀
    prefix = f"[魔力值:{magic_value}%]"
    
    try:
        bot = get_bot()
        # 获取机器人加入的所有群
        groups = await bot.get_group_list()
        
        for group in groups:
            try:
                group_id = group["group_id"]
                # 获取机器人在该群的信息
                info = await bot.get_group_member_info(group_id=group_id, user_id=bot.self_id)
                current_card = info.get("card", "")
                
                # 如果current_card为None，将其设置为空字符串
                if current_card is None:
                    current_card = ""
                
                # 如果没有保存过这个群的原始名片，就保存它
                if group_id not in original_cards:
                    if INITIAL_CARD is not None:
                        # 使用设置的初始群名片
                        original_cards[group_id] = INITIAL_CARD
                    else:
                        # 如果当前名片已经包含魔力值或CPU信息，去掉它再保存
                        if current_card.startswith("[魔力值:") or current_card.startswith("[CPU:"):
                            original_cards[group_id] = current_card[current_card.index("]")+1:].lstrip()
                            if original_cards[group_id].startswith("[CPU:"):
                                original_cards[group_id] = original_cards[group_id][original_cards[group_id].index("]")+1:].lstrip()
                        else:
                            original_cards[group_id] = current_card
                
                # 使用保存的原始名片创建新名片
                new_card = prefix + " " + original_cards[group_id]
                
                # 更新群名片
                await bot.set_group_card(group_id=group_id, user_id=bot.self_id, card=new_card)
                
                # 日志打印新的标签信息
                #nonebot.logger.info(f"群 {group_id} 的新群名片: {new_card}")
            except Exception as e:
                nonebot.logger.error(f"更新群 {group_id} 的群名片时发生错误: {e}")
    except Exception as e:
        nonebot.logger.error(f"获取机器人或群列表时发生错误: {e}")

# 插件元数据
__plugin_meta__ = {
    "name": "CPU使用率和魔力值群名片更新",
    "description": "每10秒更新机器人群名片,在前面显示当前魔力值和CPU使用率",
    "usage": "该插件自动运行,无需手动触发"
}
