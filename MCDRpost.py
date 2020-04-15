# -*- coding: utf-8 -*-

# nextid由GetNextId方法获取
# 发件/收件/取消后将ids列表排序后，将nextid设为缺少的值或+1
# 当len(ids)%saveDelay==0时保存orders.json
# 服务器开启时读取orders.json,若无该文件则创建
# 服务器关闭时保存orders.json
#
# data get entity @s Inventory[{Slot: -106b}]
# replaceitem entity @s weapon.offhand minecraft:diamond_pickaxe{Enchantments: [{lvl: 3 s,id: "minecraft:unbreaking"}]}

# PlayerInfoAPI = server.get_plugin_instance('PlayerInfoAPI')
# inventory = PlayerInfoAPI.getPlayerInfo(server, info.player, 'Inventory[{Slot:-106b}]')
# if type(inventory) == dict:
#     server.logger.info(inventory)

# {'Slot': -106, 'id': 'minecraft:diamond_pickaxe', 'Count': 1, 'tag': {'Damage': 0, 'Enchantments': [{'lvl': 3, 'id': 'minecraft:unbreaking'}]}}

import json
import time

Prefix = '!!po'
# nextid = 1
saveDelay = 5
orders = {
    'players': [],
    'ids': [0]
}
helpmsg = '''-------- MCDRpost --------
一个用于邮寄/传送物品的MCDR插件
§a『命令说明』§r
§7{0}§r 显示帮助信息
§7{0} p §e[<收件人id>] §b[<备注>] §r 将副手物品发送给§e[收件人]§r。§b[备注]§r为可选项
§7{0} r§r 列出收件列表
§7{0} r §6[<单号>]§r 确认收取该单号的物品到副手(收取前将副手清空)§r
§7{0} pl§r 列出发件(待收取)列表
§7{0} c §6[<单号>]§r 取消传送物品(收件人还未收件前)，该单号物品退回到副手(取消前将副手清空)§r
'''.format(Prefix)

def getNextId():
    nextid = 1
    orders['ids'].sort()
    for i, id in enumerate(orders['ids']):
        if i != id:
            nextid = i
            orders['ids'].append(nextid)
            return nextid
    nextid = len(orders['ids'])
    orders['ids'].append(nextid)
    return nextid

def format_time():
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def checkPlayer(player):
    for id in orders['players']:
        if id == player:
            return True
    return False

def getOffhandItem(server, player):
    PlayerInfoAPI = server.get_plugin_instance('PlayerInfoAPI')
    offhandItem = PlayerInfoAPI.getPlayerInfo(server, player, 'Inventory[{Slot:-106b}]')
    if type(offhandItem) == dict:
        return offhandItem
    else:
        return None

def delOrder(server, id):
    try:
        orders.pop(id)
    except Exception:
        server.logger.info("Error occurred during delete one PostOrder")

def receiveItem(server, player, orderid):
    if getOffhandItem(server, player) == None:
        try:
            order = orders[orderid]
        except KeyError:
            server.tell(player, '* 单号错误，请检查您的输入')
            return
        server.execute('replaceitem entity '+ player + ' weapon.offhand ' + order.item)
        delOrder(server, orderid)
    else:
        server.tell(player, '* 抱歉，请先将您的副手物品清空')
        return

def postItem(server, info):
    # !!po receiver infomsg
    sender = info.player
    itemjson = getOffhandItem(server, sender)
    infomsg = "无备注信息"
    if len(info.content.split()) >= 3:
        receiver = info.content.split()[2]
    else:
        server.tell(sender, '* 您的输入有误，命令 !!po 可查看帮助信息')
        return
    if len(info.content.split()) >= 4:
        infomsg = info.content.split()[3]
    if not checkPlayer(receiver):
        server.tell(sender, '* 收件人 '+receiver+' 未曾进服，不在登记玩家内，不可被发送，请检查您的输入')
        return
    if sender == receiver:
        server.tell(sender, '* 寄件人和收件人不能为同一人~')
        return
    if itemjson == None:
        server.tell(sender, '* 副手检测不到可寄送的物品，请检查副手')
        return
    else:
        item = str(itemjson['id']) + str(itemjson['tag']) + ' ' + str(itemjson['Count'])
        orders[getNextId()] = {
            'time': format_time(),
            'sender': sender,
            'receiver': receiver,
            'item': item,
            'info': infomsg
        }
        server.execute('replaceitem entity '+sender+' weapon.offhand minecraft:air')
        server.tell(sender, '* 物品存放于中转站，等待对方接收\n* 使用 !!po pl 可以查看还未被查收的发件列表')


def on_info(server, info):
    if info.is_user:
        if info.content == '!!po':
            server.reply(info, helpmsg)
        elif info.content.startswith('!!po p '):
            postItem(server, info)