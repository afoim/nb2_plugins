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
            # 从 ip-api.com 获取公网 IP
            ip_response = await client.get("http://ip-api.com/json")
            ip_response.raise_for_status()
            ip_data = ip_response.json()

            if ip_data.get("status") == "fail":
                await get_ip_info.finish("获取公网 IP 信息失败，请稍后再试。")

            ipv4_address = ip_data.get("query", "未知")

            # 使用获取的 IP 地址调用美图 API
            location_response = await client.get(f"https://webapi-pc.meitu.com/common/ip_location?ip={ipv4_address}")
            location_response.raise_for_status()
            location_data = location_response.json()

            if location_data.get("code") != 0:
                await get_ip_info.finish("获取位置信息失败，请稍后再试。")

            # 获取位置信息
            location_info = location_data['data'].get(ipv4_address, {})
            area_code = location_info.get("area_code", "未知")
            city = location_info.get("city", "未知")
            province = location_info.get("province", "未知")
            nation = location_info.get("nation", "未知")
            isp = location_info.get("isp", "未知")

            result_info = (
                f"开盒喵！开盒喵！二叉树树住在？！\n"
                f"公网IPv4: {ipv4_address}\n"
                f"城市: {city}\n"
                f"省份: {province}\n"
                f"国家: {nation}\n"
                f"ISP: {isp}\n"
                f"区号: {area_code}"
            )
            await get_ip_info.finish(result_info)

        except Exception as e:
            return
