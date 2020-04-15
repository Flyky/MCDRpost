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
maxPostNum = 5
saveDelay = 1
orders = {
    'players': [],
    'ids': [0]
}
OrderJsonFile = './plugins/PostOrders.json'

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
            return str(nextid)
    nextid = len(orders['ids'])
    orders['ids'].append(nextid)
    return str(nextid)

def loadOrdersJson():
    global orders
    try:
        with open(OrderJsonFile) as f:
            orders = json.load(f, encoding='utf8')
    except:
        return

def saveOrdersJson():
    global orders
    try:
        with open(OrderJsonFile, 'w') as f:
            json.dump(orders, f, indent=4)
    except:
        return

def regularSaveOrderJson():
    if len(orders['ids']) % saveDelay == 0:
        saveOrdersJson()

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
    global orders
    try:
        orders.pop(id)
        orders['ids'].remove(int(id))
    except Exception:
        server.logger.info("Error occurred during delete one PostOrder")
        return False

def getItem(server, player, orderid):
    if not getOffhandItem(server, player):
        order = orders.get(orderid, -1)
        server.execute('replaceitem entity '+ player + ' weapon.offhand ' + str(order['item']))
        delOrder(server, orderid)
        return True
    else:
        server.tell(player, '* 抱歉，请先将您的副手物品清空')
        return False

def postItem(server, info):
    # !!po receiver infomsg
    sender = info.player
    itemjson = getOffhandItem(server, sender)
    infomsg = "无备注信息"
    postId = None
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
    if not itemjson:
        server.tell(sender, '* 副手检测不到可寄送的物品，请检查副手')
        return
    else:
        item = str(itemjson['id']) + str(itemjson['tag']) + ' ' + str(itemjson['Count'])
        postId = getNextId()
        orders[postId] = {
            'time': format_time(),
            'sender': sender,
            'receiver': receiver,
            'item': item,
            'info': infomsg
        }
        server.execute('replaceitem entity '+sender+' weapon.offhand minecraft:air')
        server.tell(sender, '* 物品存放于中转站，等待对方接收\n* 使用 !!po pl 可以查看还未被查收的发件列表')
        server.tell(receiver, '[MCDRpost] 您有一件新快件，命令 !!po rl 查看收件箱\n* 命令 !!po r '+postId+' 直接收取该快件')
        regularSaveOrderJson()

def cancelOrder(server, info):
    # !!po c orderid
    player = info.player
    orderid = None
    if len(info.content.split()) >= 3:
        orderid = info.content.split()[2]
    else:
        server.tell(player,'* 未输入需要取消的单号，!!po 可查看帮助信息')
        return False
    try:
        if not player == orders[orderid]['sender']:
            server.tell(player,'* 该订单非您寄送，您无权对其操作，请检查输入')
            return False
    except KeyError:
        server.tell(player,'* 未查询到该单号，请检查输入')
        return False
    if not getItem(server, player, orderid):
        return False
    server.tell(player,'* 已成功取消订单 '+orderid+'，物品回收至副手')
    regularSaveOrderJson()

def receiveItem(server, info):
    # !!po c orderid
    player = info.player
    orderid = None
    if len(info.content.split()) >= 3:
        orderid = info.content.split()[2]
    else:
        server.tell(player,'* 未输入需要取消的单号，!!po 可查看帮助信息')
        return
    try:
        if not player == orders[orderid]['receiver']:
            server.tell(player,'* 该订单您非收件人，您无权对其操作，请检查输入')
            return
    except KeyError:
        server.tell(player,'* 未查询到该单号，请检查输入')
        return
    getItem(server, player, orderid)
    server.tell(player,'* 已成功收取快件 '+orderid+'，物品接收至副手')
    regularSaveOrderJson()

def on_info(server, info):
    if info.is_user:
        if info.content == '!!po':
            server.reply(info, helpmsg)
        elif info.content.startswith('!!po p '):
            postItem(server, info)
        elif info.content == '!!po pl':
            pass
        elif info.content.startswith('!!po r '):
            pass
        elif info.content == '!!po rl':
            pass
        elif info.content.startswith('!!po c '):
            cancelOrder(server, info)

def on_load(server, old_module):
    loadOrdersJson()

def on_server_startup(server):
    loadOrdersJson()

def on_server_stop(server):
    saveOrdersJson()

def on_player_joined(server, player):
    global orders
    flag = True
    for id in orders['players']:
        if id == player:
            flag = False
    if flag:
        orders['players'].append(player)
        server.logger.info('[MCDRpost] 已登记玩家 '+player)
        saveOrdersJson()