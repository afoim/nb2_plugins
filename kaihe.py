import httpx
from nonebot import on_command, Bot
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="获取公网IP和位置信息",
    description="获取当前的公网IPv4地址以及位置信息",
    usage="/获取公网IP"
)

get_ip_info = on_command("开盒")

@get_ip_info.handle()
async def handle_get_ip(bot: Bot):
    async with httpx.AsyncClient() as client:
        try:
            # 从 ip.useragentinfo.com 获取公网 IP 和位置信息
            response = await client.get("https://ip.useragentinfo.com/json")
            response.raise_for_status()
            ip_info = response.json()

            result_info = (
                f"开盒喵！开盒喵！二叉树树住在？！\n"
                f"国家：{ip_info.get('country', '未知')}\n"
                f"省份：{ip_info.get('province', '未知')}\n"
                f"城市：{ip_info.get('city', '未知')}\n"
                f"ISP：{ip_info.get('isp', '未知')}\n"
                f"网络类型：{ip_info.get('net', '未知')}\n"
                f"IP：{ip_info.get('ip', '未知')}\n"
            )
            await get_ip_info.finish(result_info)

        except Exception as e:
            return
