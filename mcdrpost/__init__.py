# -*- coding: utf-8 -*-

import json
import time
import os

from mcdreforged.api.all import *
from mcdrpost.OrdersData import orders

Prefix = '!!po'
maxStorageNum = 5   # 最大存储订单量，设为-1则无限制
saveDelay = 1

OrderJsonDirectory = './config/MCDRpost/'
OrderJsonFile = OrderJsonDirectory + 'PostOrders.json'

def loadOrdersJson(logger: MCDReforgedLogger):
    if not os.path.isfile(OrderJsonFile):
        logger.info('[MCDRpost] 未找到数据文件，自动生成')
        os.makedirs(OrderJsonDirectory)
        with open(OrderJsonFile, 'w+') as f:
            f.write('{"players": [], "ids":[]}')

    orders.load_json(OrderJsonFile)


def print_help_message(source: CommandSource):
    pass


def register_command(server: PluginServerInterface):
    server.register_command(
        Literal(Prefix).runs(print_help_message)
    )


def on_load(server: PluginServerInterface, old):
    loadOrdersJson(server.logger)
    server.register_help_message(Prefix, {
        "en_us": "post/teleport weapon hands items",
        "zh_cn": "传送/收寄副手物品"
    })
    register_command(server)


def on_server_startup(server):
    loadOrdersJson(server)