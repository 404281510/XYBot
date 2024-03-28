import json

import aiohttp
import yaml
from loguru import logger
from prettytable import PrettyTable

import pywxdll
from utils.plugin_interface import PluginInterface


class get_chatroom_memberlist(PluginInterface):
    def __init__(self):
        config_path = "plugins/get_chatroom_memberlist.yml"
        with open(config_path, "r", encoding="utf-8") as f:  # 读取设置
            config = yaml.safe_load(f.read())

        self.information_post_url = config[
            "information_post_url"
        ]  # 获取信息发送api的url (非微信)

        main_config_path = "main_config.yml"
        with open(main_config_path, "r", encoding="utf-8") as f:  # 读取设置
            main_config = yaml.safe_load(f.read())

        self.ip = main_config["ip"]  # 机器人ip
        self.port = main_config["port"]  # 机器人端口
        self.bot = pywxdll.Pywxdll(self.ip, self.port)  # 机器人api

        self.admin_list = main_config["admins"]  # 获取管理员列表

    async def run(self, recv):
        if recv['id1']:
            admin_wxid = recv['id1']
        else:
            admin_wxid = recv['wxid']

        error = ''
        if admin_wxid not in self.admin_list:
            error = "-----XYBot-----\n❌你配用这个指令吗？"
        elif recv['id1'] and recv['wxid']:
            error = "-----XYBot-----\n⚠️私聊无法使用这个命令！"

        if not error:  # 判断操作元是否是管理员
            heading = ["名字", "wxid"]
            chart = PrettyTable(heading)  # 创建列表

            data = self.bot.get_chatroom_memberlist(recv["wxid"])

            for member_wxid in data["member"]:  # for循环成员列表
                name = self.bot.get_chatroom_nickname(recv["wxid"], member_wxid)[
                    "nick"
                ]  # 获取成员昵称
                chart.add_row([name, member_wxid])  # 加入表格中

            chart.align = "l"
            # 不传直接发微信是因为微信一行实在太少了，不同设备还不一样，用pywxdll发excel文件会报错
            json_data = json.dumps(
                {"content": chart.get_string()}
            )  # 转成json格式 用于发到api
            url = self.information_post_url + "/texts"  # 组建url
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36",
            }

            conn_ssl = aiohttp.TCPConnector(verify_ssl=False)
            async with aiohttp.request(
                    "POST", url=url, data=json_data, headers=headers, connector=conn_ssl
            ) as req:
                reqeust = await req.json()
            await conn_ssl.close()

            fetch_code = reqeust["fetch_code"]  # 从api获取提取码
            date_expire = reqeust["date_expire"]  # 从api获取过期时间

            fetch_link = f"{self.information_post_url}/r/{fetch_code}"  # 组建提取链接
            out_message = f"-----XYBot-----\n🤖️本群聊的群员列表：\n{fetch_link}\n过期时间：{date_expire}"  # 组建输出信息

            self.bot.send_txt_msg(recv["wxid"], out_message)  # 发送
            logger.info(f'[发送信息]{out_message}| [发送到] {recv["wxid"]}')

        else:  # 操作人不是管理员
            out_message = error
            logger.info(f'[发送信息]{out_message}| [发送到] {recv["wxid"]}')
            self.bot.send_txt_msg(recv["wxid"], out_message)
