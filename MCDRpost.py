# -*- coding: utf-8 -*-

import json
import time
import os
import shutil

from utils.rtext import *

Prefix = '!!po'
maxStorageNum = 5   # 最大存储订单量，设为-1则无限制
saveDelay = 1
orders = {
    'players': [],
    'ids': [0]
}
OrderJsonDirectory = './plugins/MCDRpost/'
OrderJsonFile = OrderJsonDirectory + 'PostOrders.json'

def getHelpMessage(server, info):
    msgs_on_helper = RText('')
    msgs_on_admin = RText('')
    if server.get_permission_level(info) > 1:
        # helper以上权限的添加信息
        msgs_on_helper = RTextList(
            RText(Prefix+' ls orders', RColor.gray).c(RAction.suggest_command, "!!po ls orders").h('点击写入聊天栏'),RText(' | 查看当前中转站内所有订单\n')
        )
    if server.get_permission_level(info) > 2:
        # admin以上权限的添加信息
        msgs_on_admin = RTextList(
            RText(Prefix+' player add §e[<玩家id>]', RColor.gray).c(RAction.suggest_command, "!!po player add ").h('点击写入聊天栏'),RText(' | 手动注册玩家到可寄送玩家列表\n'),
            RText(Prefix+' player remove §e[<玩家id>]', RColor.gray).c(RAction.suggest_command, "!!po player remove ").h('点击写入聊天栏'),RText(' | 删除某注册的玩家\n'),
        )
    return RTextList(
        RText('--------- §3MCDRpost §r---------\n'),
        RText('一个用于邮寄/传送物品的MCDR插件\n'),
        RText('§a『命令说明』§r\n'),
        RText(Prefix, RColor.gray).c(RAction.suggest_command, "!!po").h('点击写入聊天栏'),RText('  | 显示帮助信息\n'),
        RText(Prefix+' p §e[<收件人id>] §b[<备注>]', RColor.gray).c(RAction.suggest_command, "!!po p ").h('点击写入聊天栏'),RText(' | 将副手物品发送给§e[收件人]§r。§b[备注]§r为可选项\n'),
        RText(Prefix+' rl', RColor.gray).c(RAction.suggest_command, "!!po rl").h('点击写入聊天栏'),RText(' | 列出收件列表\n'),
        RText(Prefix+' r §6[<单号>]', RColor.gray).c(RAction.suggest_command, "!!po r ").h('点击写入聊天栏'),RText(' | 确认收取该单号的物品到副手(收取前将副手清空)\n'),
        RText(Prefix+' pl', RColor.gray).c(RAction.suggest_command, "!!po pl").h('点击写入聊天栏'),RText(' | 列出收件列表\n'),
        RText(Prefix+' c §6[<单号>]', RColor.gray).c(RAction.suggest_command, "!!po c ").h('点击写入聊天栏'),RText(' | 取消传送物品(收件人未收件前)，该单号物品退回到副手(取消前请将副手清空)\n'),
        RText(Prefix+' ls players', RColor.gray).c(RAction.suggest_command, "!!po ls players").h('点击写入聊天栏'),RText(' | 查看可被寄送的注册玩家列表\n'),
        msgs_on_helper,
        msgs_on_admin,
        RText('-----------------------')
    )

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

def loadOrdersJson(server):
    global orders
    if not os.path.isfile(OrderJsonFile):
        server.logger.info('[MCDRpost] 未找到数据文件，自动生成')
        os.makedirs(OrderJsonDirectory)
        with open(OrderJsonFile, 'w+') as f:
            f.write('{"players": [], "ids":[]}')
    if os.path.exists('./plugins/PostOrders.json'):
        # v0.1.1的插件数据文件位置移动
        shutil.move('./plugins/PostOrders.json', OrderJsonFile)
    try:
        with open(OrderJsonFile) as f:
            orders = json.load(f, encoding='utf8')
    except:
        return

def saveOrdersJson():
    global orders
    try:
        with open(OrderJsonFile, 'w+') as f:
            json.dump(orders, f, indent=4)
        server.logger.info("[MCDRpost] Saved OrderJsonFile")
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

def checkOrderOnPlayerJoin(player):
    for orderid in orders['ids']:
        try:
            order = orders[str(orderid)]
        except:
            continue
        if order.get('receiver') == player:
            return True
    return False

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
        server.execute('execute at ' + player + ' run playsound minecraft:entity.bat.takeoff player ' + player)
        delOrder(server, orderid)
        return True
    else:
        server.tell(player, '§e* 抱歉，请先将您的§6副手物品§e清空')
        return False

def postItem(server, info):
    # !!po receiver infomsg
    sender = info.player
    itemjson = getOffhandItem(server, sender)
    infomsg = "无备注信息"
    postId = None
    if not checkStorage(sender):
        server.tell(sender, '§e* 您当前存放在中转站的订单数已达到了上限:'+str(maxStorageNum)+'\n命令 §7!!po pl §e查看您在中转站内的发件订单')
        return
    if len(info.content.split()) >= 3:
        receiver = info.content.split()[2]
    else:
        server.tell(sender, '§e* 您的输入有误，命令 §7!!po §e可查看帮助信息')
        return
    if len(info.content.split()) >= 4:
        infomsg = info.content.split()[3]
    if not checkPlayer(receiver):
        server.tell(sender, '§e* 收件人 §b'+receiver+' §e未曾进服，不在登记玩家内，不可被发送，请检查您的输入')
        return
    if sender == receiver:
        server.tell(sender, '§e* 寄件人和收件人不能为同一人~')
        return
    if not itemjson:
        server.tell(sender, '§e* 副手检测不到可寄送的物品，请检查副手')
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
        server.tell(sender, '§6* 物品存放于中转站，等待对方接收\n* 使用 §7!!po pl §6可以查看还未被查收的发件列表')
        server.execute('execute at ' + sender + ' run playsound minecraft:entity.arrow.hit_player player ' + sender)
        server.tell(receiver, '§6[MCDRpost] §e您有一件新快件，命令 §7!!po rl §e查看收件箱\n* 命令 §7!!po r '+postId+' §e直接收取该快件')
        server.execute('execute at ' + receiver + ' run playsound minecraft:entity.arrow.shoot player ' + receiver)
        regularSaveOrderJson()

def cancelOrder(server, info):
    # !!po c orderid
    player = info.player
    orderid = None
    if len(info.content.split()) >= 3:
        orderid = info.content.split()[2]
    else:
        server.tell(player,'§e* 未输入需要取消的单号，§7!!po §e可查看帮助信息')
        return False
    try:
        if not player == orders[orderid]['sender']:
            server.tell(player,'§e* 该订单非您寄送，您无权对其操作，请检查输入')
            return False
    except KeyError:
        server.tell(player,'§e* 未查询到该单号，请检查输入')
        return False
    if not getItem(server, player, orderid):
        return False
    server.tell(player,'§e* 已成功取消订单 '+orderid+'，物品回收至副手')
    regularSaveOrderJson()

def receiveItem(server, info):
    # !!po c orderid
    player = info.player
    orderid = None
    if len(info.content.split()) >= 3:
        orderid = info.content.split()[2]
    else:
        server.tell(player,'§e* 未输入需要取消的单号，§7!!po §e可查看帮助信息')
        return False
    try:
        if not player == orders[orderid]['receiver']:
            server.tell(player,'§e* 您非该订单收件人，无权对其操作，请检查输入')
            return False
    except KeyError:
        server.tell(player,'§e* 未查询到该单号，请检查输入')
        return False
    if not getItem(server, player, orderid):
        return False
    server.tell(player,'§e* 已成功收取快件 '+orderid+'，物品接收至副手')
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
        server.tell(info.player,'§6* 您当前没有快件订单在中转站~')
        return
    listmsg = '''==========================================
    单号    |   收件人  |   发件时间  |   备注信息
    {0}
    -------------------------------------------
    §6使用命令 §7!!po c [单号] §6取消快件§r
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
        server.tell(info.player,'§e* 您当前没有待收快件~')
        return
    listmsg = '''==========================================
    单号    |   发件人  |   发件时间  |   备注信息
    {0}
    -------------------------------------------
    §6使用命令 §7!!po r [单号] §6来接收快件物品§r
==========================================='''.format(listmsg)
    server.tell(info.player, listmsg)

def listOrders(server, info):
    # !!po ls orders
    listmsg = ''
    if server.get_permission_level(info) < 2:
        listmsg = '§c* 抱歉，您没有权限使用该命令'
    else:
        for orderid in orders['ids']:
            order = orders.get(str(orderid))
            if not order:
                continue
            listmsg = listmsg+str(orderid)+'  | '+order.get('sender')+'  | '+order.get('receiver')+'  | '+order.get('time')+'  | '+order.get('info')+'\n    '
        if listmsg == '':
            server.reply(info,'§6* 中转站内无任何快件~')
            return
        listmsg = '''==========================================
 单号    |   发件人  |   收件人  |   发件时间  |   备注信息
{0}
==========================================='''.format(listmsg)
    server.reply(info, listmsg)

def listPlayers(server, info):
    # !!po ls players
    if server.get_permission_level(info) < 1:
        server.tell(info.player, '§c* 抱歉，您没有权限使用该命令')
        return
    server.reply(info, '§6[MCDRpost] §e可寄送的注册玩家列表：\n§r' + str(orders.get('players')))

def removePlayerInList(server, info):
    global orders
    playerId = ''
    if server.get_permission_level(info) < 3:
        server.tell(info.player, '§c* 抱歉，您没有权限使用该命令')
        return
    if len(info.content.split()) == 4:
        playerId = info.content.split()[3]
    else:
        server.tell(info.player,'§4* 玩家id格式有误，请检查后再输入')
        return False

    if orders.get('players').count(playerId) == 0:
        server.tell(info.player,'§4* 该玩家未注册，无法进行删除 \n§r使用 §7!!po ls players §r可以查看所有注册玩家列表')
        return
    orders.get('players').remove(playerId)
    server.tell(info.player,'§e[MCDRpost] §a成功删除玩家 §b'+playerId+' §a,使用 §7!!po ls players §a可以查看所有注册玩家列表')
    server.logger.info('[MCDRpost] 已删除登记玩家 '+playerId)
    saveOrdersJson()

def addPlayerToList(server, info):
    global orders
    playerId = ''
    if server.get_permission_level(info) < 3:
        server.tell(info.player, '§c* 抱歉，您没有权限使用该命令')
        return
    if len(info.content.split()) == 4:
        playerId = info.content.split()[3]
    else:
        server.tell(info.player,'§4* 玩家id格式有误，请检查后再输入')
        return False

    if orders.get('players').count(playerId) != 0:
        server.tell(info.player,'§4* 该玩家已注册，请检查后再输入 \n§r使用 §7!!po ls players §r可以查看所有注册玩家列表')
        return
    orders.get('players').append(playerId)
    server.tell(info.player,'§e[MCDRpost] §a成功注册玩家 §b'+playerId+' §a,使用 §7!!po ls players §a可以查看所有注册玩家列表')
    server.logger.info('[MCDRpost] 已登记玩家 '+playerId)
    saveOrdersJson()

def on_info(server, info):
    if info.is_user:
        if info.content == Prefix:
            server.reply(info, getHelpMessage(server, info))
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
        elif info.content == Prefix+' ls orders':
            listOrders(server, info)
        elif info.content == Prefix+' ls players':
            listPlayers(server, info)
        elif info.content.startswith(Prefix+' player add '):
            addPlayerToList(server, info)
        elif info.content.startswith(Prefix+' player remove '):
            removePlayerInList(server, info)

def on_load(server, old_module):
    loadOrdersJson(server)
    server.add_help_message(Prefix, "传送/收寄副手物品")

def on_server_startup(server):
    loadOrdersJson(server)

def on_player_joined(server, player):
    global orders
    flag = True
    for id in orders['players']:
        if id == player:
            flag = False
            if checkOrderOnPlayerJoin(player):
                time.sleep(3)   # 延迟 3s 后再提示，防止更多进服消息混杂而看不到提示
                server.tell(player, "§6[MCDRpost] §e您有待查收的快件~ 命令 §7!!po rl §e查看详情")
                server.execute('execute at ' + player + ' run playsound minecraft:entity.arrow.hit_player player ' + player)
    if flag:
        orders['players'].append(player)
        server.logger.info('[MCDRpost] 已登记玩家 '+player)
        saveOrdersJson()