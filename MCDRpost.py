# -*- coding: utf-8 -*-

import json
import time

Prefix = '!!po'
maxStorageNum = 5   # 最大存储订单量，设为-1则无限制
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
§7{0} rl§r 列出收件列表
§7{0} r §6[<单号>]§r 确认收取该单号的物品到副手(收取前将副手清空)§r
§7{0} pl§r 列出发件(待收取)列表
§7{0} c §6[<单号>]§r 取消传送物品(收件人还未收件前)，该单号物品退回到副手(取消前请将副手清空)§r
------------------'''.format(Prefix)

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

def checkStorage(player):
    num = 0
    if maxStorageNum < 0:
        return True
    for orderid in orders['ids']:
        try:
            order = orders[str(orderid)]
        except:
            continue
        if order.get('sender') == player:
            num += 1
            if num >= maxStorageNum:
                return False
    return True

def getOffhandItem(server, player):
    PlayerInfoAPI = server.get_plugin_instance('PlayerInfoAPI')
    try: 
        offhandItem = PlayerInfoAPI.getPlayerInfo(server, player, 'Inventory[{Slot:-106b}]')
        if type(offhandItem) == dict:
            return offhandItem
        else:
            return None
    except:
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
    if not checkStorage(sender):
        server.tell(sender, '* 您当前存放在中转站的订单数已达到了上限:'+str(maxStorageNum)+'\n命令 !!po pl 查看您在中转站内的发件订单')
        return
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
        item = str(itemjson.get('id')) + str(itemjson.get('tag', '')) + ' ' + str(itemjson.get('Count', ''))
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
            server.tell(player,'* 您非该订单收件人，无权对其操作，请检查输入')
            return
    except KeyError:
        server.tell(player,'* 未查询到该单号，请检查输入')
        return
    getItem(server, player, orderid)
    server.tell(player,'* 已成功收取快件 '+orderid+'，物品接收至副手')
    regularSaveOrderJson()

def listOutbox(server, info):
    listmsg = ''
    for orderid in orders['ids']:
        order = orders.get(str(orderid))
        if not order:
            continue
        if order.get('sender') == info.player:
            listmsg = listmsg+str(orderid)+'  | '+order.get('receiver')+'  | '+order.get('time')+'  | '+order.get('info')+'\n    '
    if listmsg == '':
        server.tell(info.player,'* 您当前没有快件订单在中转站~')
        return
    listmsg = '''==========================================
    单号    |   收件人  |   发件时间  |   备注信息
    {0}
    -------------------------------------------
    使用命令 !!po c [单号] 取消快件
==========================================='''.format(listmsg)
    server.tell(info.player, listmsg)

def listInbox(server, info):
    listmsg = ''
    for orderid in orders['ids']:
        order = orders.get(str(orderid))
        if not order:
            continue
        if order.get('receiver') == info.player:
            listmsg = listmsg+str(orderid)+'  | '+order.get('sender')+'  | '+order.get('time')+'  | '+order.get('info')+'\n    '
    if listmsg == '':
        server.tell(info.player,'* 您当前没有待收快件~')
        return
    listmsg = '''==========================================
    单号    |   发件人  |   发件时间  |   备注信息
    {0}
    -------------------------------------------
    使用命令 !!po r [单号] 来接收快件物品
==========================================='''.format(listmsg)
    server.tell(info.player, listmsg)


def on_info(server, info):
    if info.is_user:
        if info.content == Prefix:
            server.reply(info, helpmsg)
        elif info.content.startswith(Prefix+' p '):
            postItem(server, info)
        elif info.content == Prefix+' pl':
            listOutbox(server, info)
        elif info.content.startswith(Prefix+' r '):
            receiveItem(server, info)
        elif info.content == Prefix+' rl':
            listInbox(server, info)
        elif info.content.startswith(Prefix+' c '):
            cancelOrder(server, info)

def on_load(server, old_module):
    loadOrdersJson()

def on_server_startup(server):
    loadOrdersJson()

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