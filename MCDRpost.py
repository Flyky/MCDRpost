# -*- coding: utf-8 -*-

# nextid由GetNextId方法获取
# 发件/收件/取消后将ids列表排序后，将nextid设为缺少的值或+1
# 当单号%save_delay==0时保存orders.json
# 服务器开启时读取orders.json,若无该文件则创建
# 服务器关闭时保存orders.json

import json
import time

Prefix = '!!po'
nextid = 1
save_delay = 5
orders = {
    'player': [],
    'ids': [0],
    'orders': []
}
helpmsg = '''-------- MCDRpost --------
一个用于邮寄/传送物品的MCDR插件
§a『命令说明』§r
§7{0}§r 显示帮助信息
§7{0} §e[<收件人id>] §b[<备注>] §r 将副手物品发送给§e[收件人]§r。§b[备注]§r为可选项
§7{0} r§r 列出收件列表
§7{0} r §6[<单号>]§r 确认收取该单号的物品到副手(收取前将副手清空)§r
§7{0} s§r 列出发件(待收取)列表
§7{0} c §6[<单号>]§r 取消传送物品(收件人还未收件前)，该单号物品退回到副手(取消前将副手清空)§r
'''.format(Prefix)

def GetNextId():
    orders['ids'].sort()
    for i, id in enumerate(orders['ids']):
        if i != id:
            return i
    return len(orders['ids'])
    