#  Copyright (c) 2024. Henry Yang
#
#  This program is licensed under the GNU General Public License v3.0.

import re

import aiohttp
import yaml
from loguru import logger
from wcferry import client

from utils.database import BotDatabase
from utils.plugin_interface import PluginInterface
from wcferry_helper import XYBotWxMsg


class pubg_info(PluginInterface):
    def __init__(self):
        config_path = "plugins/command/pubg_info.yml"
        with open(config_path, "r", encoding="utf-8") as f:  # 读取设置
            config = yaml.safe_load(f.read())



        self.db = BotDatabase()

    async def run(self, bot: client.Wcf, recv: XYBotWxMsg):
        recv.content = re.split(" |\u2005", recv.content)  # 拆分消息

        error = ''
        if len(recv.content) != 2:
            error = '指令格式错误！'

        if not error:
            # 首先请求geoapi，查询城市的id
            pubgName = recv.content[1]
            geo_api_url = f'http://localhost:8011/testPUBG.do?pubgName={pubgName}'

            conn_ssl = aiohttp.TCPConnector(verify_ssl=False)
            async with aiohttp.request('GET', url=geo_api_url, connector=conn_ssl) as response:
                geoapi_json = await response.json()
                await conn_ssl.close()
            out_message = f'{geoapi_json}'
            await self.send_friend_or_group(bot, recv, out_message)
        else:
            await self.send_friend_or_group(bot, recv, error)

    async def send_friend_or_group(self, bot: client.Wcf, recv: XYBotWxMsg, out_message="null"):
        if recv.from_group():  # 判断是群还是私聊
            out_message = f"@{self.db.get_nickname(recv.sender)}\n{out_message}"
            logger.info(f'[发送@信息]{out_message}| [发送到] {recv.roomid}')
            bot.send_text(out_message, recv.roomid, recv.sender)  # 发送@信息
        else:
            logger.info(f'[发送信息]{out_message}| [发送到] {recv.roomid}')
            bot.send_text(out_message, recv.roomid)  # 发送

    @staticmethod
    def compose_weather_message(city_name, now_weather_api_json, weather_forecast_api_json):
        update_time = now_weather_api_json['updateTime']
        now_temperature = now_weather_api_json['now']['temp']
        now_feelslike = now_weather_api_json['now']['feelsLike']
        now_weather = now_weather_api_json['now']['text']
        now_wind_direction = now_weather_api_json['now']['windDir']
        now_wind_scale = now_weather_api_json['now']['windScale']
        now_humidity = now_weather_api_json['now']['humidity']
        now_precip = now_weather_api_json['now']['precip']
        now_visibility = now_weather_api_json['now']['vis']
        now_uvindex = weather_forecast_api_json['daily'][0]['uvIndex']

        message = f'-----XYBot-----\n{city_name} 实时天气☁️\n更新时间：{update_time}⏰\n\n🌡️当前温度：{now_temperature}℃\n🌡️体感温度：{now_feelslike}℃\n☁️天气：{now_weather}\n☀️紫外线指数：{now_uvindex}\n🌬️风向：{now_wind_direction}\n🌬️风力：{now_wind_scale}级\n💦湿度：{now_humidity}%\n🌧️降水量：{now_precip}mm/h\n👀能见度：{now_visibility}km\n\n☁️未来3天 {city_name} 天气：\n'
        for day in weather_forecast_api_json['daily'][1:4]:
            date = '.'.join([i.lstrip('0') for i in day['fxDate'].split('-')[1:]])
            weather = day['textDay']
            max_temp = day['tempMax']
            min_temp = day['tempMin']
            uv_index = day['uvIndex']
            message += f'{date} {weather} 最高🌡️{max_temp}℃ 最低🌡️{min_temp}℃ ☀️紫外线:{uv_index}\n'

        return message
