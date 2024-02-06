import os

import pywxdll
import yaml
from loguru import logger

import database
from plugin_interface import PluginInterface


class admin_signin_reset(PluginInterface):
    def __init__(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        main_config_path = os.path.join(current_directory, '../main_config.yml')
        with open(main_config_path, 'r', encoding='utf-8') as f:  # 读取设置
            main_config = yaml.safe_load(f.read())

        self.ip = main_config['ip']  # 获取机器人api的ip
        self.port = main_config['port']  # 获取机器人api的端口
        self.bot = pywxdll.Pywxdll(self.ip, self.port)  # 机器人api

        self.admin_list = main_config['admins']  # 获取管理员列表

        self.db = database.BotDatabase()  # 实例化数据库类

    async def run(self, recv):
        if recv['id1']:  # 判断是群还是私聊
            admin_wxid = recv['id1']  # 是群
        else:
            admin_wxid = recv['wxid']  # 是私聊

        if admin_wxid in self.admin_list:  # 如果操作人在白名单内
            self.db.reset_stat()  # 重置数据库签到状态
            out_message = '-----XYBot-----\n😊成功重置签到状态！'
            logger.info('[发送信息]{out_message}| [发送到] {wxid}'.format(out_message=out_message, wxid=recv['wxid']))
            self.bot.send_txt_msg(recv['wxid'], out_message)  # 发送信息
        else:  # 操作人不在白名单内
            out_message = '-----XYBot-----\n❌你配用这个指令吗？'
            logger.info('[发送信息]{out_message}| [发送到] {wxid}'.format(out_message=out_message, wxid=recv['wxid']))
            self.bot.send_txt_msg(recv['wxid'], out_message)  # 发送信息
