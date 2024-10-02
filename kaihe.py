import httpx
from nonebot import on_command, Bot
from nonebot.adapters.onebot.v11 import Message
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
            # 获取位置信息
            response = await client.get("http://ip-api.com/json")
            response.raise_for_status()  # 检查响应状态
            data = response.json()

            if data.get("status") == "fail":
                await get_ip_info.finish("获取IP信息失败，请稍后再试。")

            ipv4_address = data.get("query", "未知")
            location = data.get("city", "未知")
            region = data.get("regionName", "未知")
            country = data.get("country", "未知")
            isp = data.get("isp", "未知")

            location_info = (
                f"开盒喵！开盒喵！\n"
                f"公网IPv4: {ipv4_address}\n"
                f"位置: {location}，{region}，{country}\n"
                f"ISP: {isp}"
            )
            await get_ip_info.finish(location_info)
        except Exception as e:
            return
