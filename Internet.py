import httpx
from nonebot import on_command, Bot
from nonebot.adapters.onebot.v11 import Message
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="获取公网IP和位置信息",
    description="获取当前的公网IPv4地址以及位置信息",
    usage="/获取公网IP"
)

get_ip_info = on_command("Internet")


@get_ip_info.handle()
async def handle_get_ip(bot: Bot):
    try:
        # 使用 httpx 请求 ip-api.com
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ip-api.com/json/")
            response.raise_for_status()
            ip_info = response.json()

        # 构建可读的消息内容
        result_info = (\
            f"调用API：http://ip-api.com/json/\n"
            f"状态：{ip_info.get('status', '未知')}\n"
            f"国家：{ip_info.get('country', '未知')} ({ip_info.get('countryCode', '未知')})\n"
            f"地区：{ip_info.get('regionName', '未知')} ({ip_info.get('region', '未知')})\n"
            f"城市：{ip_info.get('city', '未知')}\n"
            f"邮编：{ip_info.get('zip', '未知')}\n"
            f"经度：{ip_info.get('lat', '未知')}\n"
            f"纬度：{ip_info.get('lon', '未知')}\n"
            f"时区：{ip_info.get('timezone', '未知')}\n"
            f"ISP：{ip_info.get('isp', '未知')}\n"
            f"组织：{ip_info.get('org', '未知')}\n"
            f"AS编号：{ip_info.get('as', '未知')}\n"
            f"IP地址：{ip_info.get('query', '未知')}"
        )

        # 发送可读的结果信息
        await get_ip_info.finish(Message(result_info))

    except httpx.RequestError as e:
        await get_ip_info.finish(f"HTTP 请求错误: {e}")
    except httpx.HTTPStatusError as e:
        await get_ip_info.finish(f"HTTP 响应错误: {e.response.status_code}")
    except Exception as e:
        return
