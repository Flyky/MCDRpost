# -*- coding: utf-8 -*-

import json
import time
import os

from mcdreforged.api.all import *
from mcdrpost.OrdersData import orders
from mcdrpost.utils import format_time, get_offhand_item, execute_replace_offhand, can_command_item

Prefix = '!!po'
MaxStorageNum = 5   # 最大存储订单量，设为-1则无限制
SaveDelay = 1
OrderJsonDirectory = './config/MCDRpost/'
OrderJsonFile = OrderJsonDirectory + 'PostOrders.json'
command_item = -2

orders.set_json_path(OrderJsonFile)
orders.set_max_storage_num(MaxStorageNum)

def loadOrdersJson(logger: MCDReforgedLogger):
    if not os.path.isfile(OrderJsonFile):
        logger.info('未找到数据文件，自动生成')
        os.makedirs(OrderJsonDirectory)
        with open(OrderJsonFile, 'w+') as f:
            f.write('{"players": [], "ids":[]}')
    orders.load_json()


def print_help_message(source: CommandSource):
    msgs_on_helper = RText('')
    msgs_on_admin = RText('')
    if source.has_permission_higher_than(1):
        # helper以上权限的添加信息
        msgs_on_helper = RTextList(
            RText(Prefix+' ls orders', RColor.gray).c(RAction.suggest_command, "!!po ls orders").h('点击写入聊天栏'),RText(' | 查看当前中转站内所有订单\n')
        )
    if source.has_permission_higher_than(2):
        # admin以上权限的添加信息
        msgs_on_admin = RTextList(
            RText(Prefix+' player add §e[<玩家id>]', RColor.gray).c(RAction.suggest_command, "!!po player add ").h('点击写入聊天栏'),RText(' | 手动注册玩家到可寄送玩家列表\n'),
            RText(Prefix+' player remove §e[<玩家id>]', RColor.gray).c(RAction.suggest_command, "!!po player remove ").h('点击写入聊天栏'),RText(' | 删除某注册的玩家\n'),
        )
    
    source.reply(
        RTextList(
            RText('--------- §3MCDRpost §r---------\n'),
            RText('一个用于邮寄/传送物品的MCDR插件\n'),
            RText('§a『命令说明』§r\n'),
            RText(Prefix, RColor.gray).c(RAction.suggest_command, "!!po").h('点击写入聊天栏'),RText('  | 显示帮助信息\n'),
            RText(Prefix+' p §e[<收件人id>] §b[<备注>]', RColor.gray).c(RAction.suggest_command, "!!po p ").h('点击写入聊天栏'),RText(' | 将副手物品发送给§e[收件人]§r。§b[备注]§r为可选项\n'),
            RText(Prefix+' rl', RColor.gray).c(RAction.suggest_command, "!!po rl").h('点击写入聊天栏'),RText(' | 列出收件列表\n'),
            RText(Prefix+' r §6[<单号>]', RColor.gray).c(RAction.suggest_command, "!!po r ").h('点击写入聊天栏'),RText(' | 确认收取该单号的物品到副手(收取前将副手清空)\n'),
            RText(Prefix+' pl', RColor.gray).c(RAction.suggest_command, "!!po pl").h('点击写入聊天栏'),RText(' | 列出发件列表\n'),
            RText(Prefix+' c §6[<单号>]', RColor.gray).c(RAction.suggest_command, "!!po c ").h('点击写入聊天栏'),RText(' | 取消传送物品(收件人未收件前)，该单号物品退回到副手(取消前请将副手清空)\n'),
            RText(Prefix+' ls players', RColor.gray).c(RAction.suggest_command, "!!po ls players").h('点击写入聊天栏'),RText(' | 查看可被寄送的注册玩家列表\n'),
            msgs_on_helper,
            msgs_on_admin,
            RText('-----------------------')
        )
    )


def regular_save_order_json(logger: MCDReforgedLogger):
    if len(orders.ids) % SaveDelay == 0:
        orders.save_to_json(logger)


def get_item(server, player, orderid):
    global command_item
    if command_item == -2:
        command_item = can_command_item(server)
    if not get_offhand_item(server, player):
        order = orders.orders.get(str(orderid), -1)
        execute_replace_offhand(server, player, order.get('item'), command_item)
        server.execute(f'execute at {player} run playsound minecraft:entity.bat.takeoff player {player}')
        orders.del_order(server.logger, orderid)
        return True
    else:
        server.tell(player, '§e* 抱歉，请先将您的§6副手物品§e清空')
        return False


######### Features #########

def post_item(src: InfoCommandSource, receiver: str, infomsg=""):
    global command_item, MaxStorageNum
    server = src.get_server()
    sender = src.get_info().player
    itemjson = get_offhand_item(server, sender)
    postId = None

    if command_item == -2:
        command_item = can_command_item(server)

    if not infomsg: infomsg="无备注信息"
    if not orders.check_storage(sender):
        src.reply(f'§e* 您当前存放在中转站的订单数已达到了上限:{MaxStorageNum}\n命令 §7!!po pl §e查看您在中转站内的发件订单')
        return
    if not orders.check_player(receiver):
        src.reply(f'§e* 收件人 §b{receiver} §e未曾进服，不在登记玩家内，不可被发送，请检查您的输入')
        return
    if sender == receiver:
        src.reply('§e* 寄件人和收件人不能为同一人~')
        return
    if not itemjson:
        src.reply('§e* 副手检测不到可寄送的物品，请检查副手')
        return
    else:
        item_tag = itemjson.get('tag', '')
        item = str(itemjson.get('id')) + \
            (json.dumps(item_tag) if len(item_tag) > 0 else '')+ ' ' + \
            str(itemjson.get('Count', ''))
        postId = orders.get_next_id()
        orders.orders[postId] = {
            'time': format_time(),
            'sender': sender,
            'receiver': receiver,
            'item': item,
            'info': infomsg
        }
        
        execute_replace_offhand(server, sender, 'minecraft:air', command_item)
        src.reply('§6* 物品存放于中转站，等待对方接收\n* 使用 §7!!po pl §6可以查看还未被查收的发件列表')
        server.execute(f'execute at {sender} run playsound minecraft:entity.arrow.hit_player player {sender}')
        server.tell(receiver, f'§6[MCDRpost] §e您有一件新快件，命令 §7!!po rl §e查看收件箱\n* 命令 §7!!po r {postId} §e直接收取该快件')
        server.execute(f'execute at {receiver} run playsound minecraft:entity.arrow.shoot player {receiver}')
        regular_save_order_json(server.logger)


def list_outbox(src: InfoCommandSource):
    player = src.get_info().player
    listmsg = ''
    for orderid in orders.ids:
        order = orders.orders.get(str(orderid))
        if not order:
            continue
        if order.get('sender') == player:
            listmsg = listmsg+str(orderid)+'  | '+order.get('receiver')+'  | '+order.get('time')+'  | '+order.get('info')+'\n    '
    if listmsg == '':
        src.reply('§6* 您当前没有快件订单在中转站~')
        return
    listmsg = '''==========================================
    单号    |   收件人  |   发件时间  |   备注信息
    {0}
    -------------------------------------------
    §6使用命令 §7!!po c [单号] §6取消快件§r
==========================================='''.format(listmsg)
    src.reply(listmsg)


def receive_item(src: InfoCommandSource, orderid):
    # !!po c orderid
    player = src.get_info().player
    server = src.get_server()
    try:
        if not player == orders.orders[str(orderid)]['receiver']:
            src.reply('§e* 您非该订单收件人，无权对其操作，请检查输入')
            return False
    except KeyError:
        src.reply('§e* 未查询到该单号，请检查输入')
        return False
    if not get_item(server, player, orderid):
        return False
    src.reply(f'§e* 已成功收取快件 {orderid}，物品接收至副手')
    regular_save_order_json(server.logger)


def list_inbox(src: InfoCommandSource):
    player = src.get_info().player
    listmsg = ''
    for orderid in orders.ids:
        order = orders.orders.get(str(orderid))
        if not order:
            continue
        if order.get('receiver') == player:
            listmsg = listmsg+str(orderid)+'  | '+order.get('sender')+'  | '+order.get('time')+'  | '+order.get('info')+'\n    '
    if listmsg == '':
        src.reply('§e* 您当前没有待收快件~')
        return
    listmsg = '''==========================================
    单号    |   发件人  |   发件时间  |   备注信息
    {0}
    -------------------------------------------
    §6使用命令 §7!!po r [单号] §6来接收快件物品§r
==========================================='''.format(listmsg)
    src.reply(listmsg)


def cancel_order(src: InfoCommandSource, orderid):
    # !!po c orderid
    player = src.get_info().player
    server = src.get_server()
    try:
        if not player == orders.orders[str(orderid)]['sender']:
            src.reply('§e* 该订单非您寄送，您无权对其操作，请检查输入')
            return False
    except KeyError:
        src.reply('§e* 未查询到该单号，请检查输入')
        return False
    if not get_item(server, player, orderid):
        return False
    src.reply(f'§e* 已成功取消订单 {orderid}，物品回收至副手')
    regular_save_order_json(server.logger)


def list_players(src: InfoCommandSource):
    # !!po ls players
    src.reply('§6[MCDRpost] §e可寄送的注册玩家列表：\n§r' + str(orders.get_players()))


def list_orders(src: InfoCommandSource):
    # !!po ls orders
    listmsg = ''
    for orderid in orders.ids:
        order = orders.orders.get(str(orderid))
        if not order:
            continue
        listmsg = listmsg+str(orderid)+'  | '+order.get('sender')+'  | '+order.get('receiver')+'  | '+order.get('time')+'  | '+order.get('info')+'\n    '
    if listmsg == '':
        src.reply('§6* 中转站内无任何快件~')
        return
    listmsg = '''==========================================
 单号    |   发件人  |   收件人  |   发件时间  |   备注信息
{0}
==========================================='''.format(listmsg)
    src.reply(listmsg)


def add_player_to_list(src: InfoCommandSource, player_id: str):
    if orders.check_player(player_id):
        src.reply('§4* 该玩家已注册，请检查后再输入 \n§r使用 §7!!po ls players §r可以查看所有注册玩家列表')
        return
    orders.add_player(player_id)
    src.reply(f'§e[MCDRpost] §a成功注册玩家 §b{player_id} §a,使用 §7!!po ls players §a可以查看所有注册玩家列表')
    src.get_server().logger.info(f'已登记玩家 {player_id}')
    orders.save_to_json(src.get_server().logger)


def remove_player_in_list(src: InfoCommandSource, player_id: str):
    if not orders.check_player(player_id):
        src.reply('§4* 该玩家未注册，无法进行删除 \n§r使用 §7!!po ls players §r可以查看所有注册玩家列表')
        return
    orders.players.remove(player_id)
    src.reply(f'§e[MCDRpost] §a成功删除玩家 §b{player_id} §a,使用 §7!!po ls players §a可以查看所有注册玩家列表')
    src.get_server().logger.info(f'已删除登记玩家 {player_id}')
    orders.save_to_json(src.get_server().logger)



def register_command(server: PluginServerInterface):
    def required_errmsg(src: CommandSource, id: int):
        if id == 1:
            src.reply('§c* 该命令仅供玩家使用')
        elif id == 2:
            src.reply('§c* 抱歉，您没有权限使用该命令')

    server.register_command(
        Literal(Prefix).
        runs(print_help_message).
        then(
            Literal('p').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            runs(lambda src: src.reply('§e* 未输入收件人，§7!!po §e可查看帮助信息')).
            then(
                Text('receiver').suggests(orders.get_players).
                runs(lambda src, ctx: post_item(src, ctx['receiver'])).
                then(
                    GreedyText('comment').
                    runs(lambda src, ctx: post_item(src, ctx['receiver'], ctx['comment']))
                )
            )
        ).
        then(
            Literal('pl').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            runs(list_outbox)
        ).
        then(
            Literal('r').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            runs(lambda src: src.reply('§e* 未输入收件单号，§7!!po §e可查看帮助信息')).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_receiver(src.get_info().player)).
                runs(lambda src, ctx: receive_item(src, ctx['orderid']))
            )
        ).
        then(
            Literal('rl').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            then(list_inbox)
        ).
        then(
            Literal('c').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            runs(lambda src: src.reply('§e* 未输入需要取消的单号，§7!!po §e可查看帮助信息')).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_sender(src.get_info().player)).
                runs(lambda src, ctx: cancel_order(src, ctx['orderid']))
            )
        ).
        then(
            Literal('ls').requires(lambda src: src.has_permission_higher_than(0)).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 2), handled=True).
            runs(lambda src: src.reply('§e* 输入命令不完整，§7!!po §e可查看帮助信息')).
            then(
                Literal('players').runs(list_players)
            ).
            then(
                Literal('orders').requires(lambda src: src.has_permission_higher_than(1)).
                on_error(RequirementNotMet, lambda src: required_errmsg(src, 2), handled=True).
                runs(list_orders)
            )
        ).
        then(
            Literal('player').requires(lambda src: src.has_permission_higher_than(2)).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 2), handled=True).
            runs(lambda src: src.reply('§e* 输入命令不完整，§7!!po §e可查看帮助信息')).
            then(
                Literal('add').
                runs(lambda src: src.reply('§e* 输入命令不完整，§7!!po §e可查看帮助信息')).
                then(
                    Text('player_id').runs(lambda src, ctx: add_player_to_list(src, ctx['player_id']))
                )
            ).
            then(
                Literal('remove').
                runs(lambda src: src.reply('§e* 输入命令不完整，§7!!po §e可查看帮助信息')).
                then(
                    Text('player_id').
                    suggests(lambda src: orders.get_players()).
                    runs(lambda src, ctx: remove_player_in_list(src, ctx['player_id']))
                )
            )
        )
    )


def on_load(server: PluginServerInterface, old):
    loadOrdersJson(server.logger)
    server.register_help_message(Prefix, {
        "en_us": "post/teleport weapon hands items",
        "zh_cn": "传送/收寄副手物品"
    })
    register_command(server)


def on_server_startup(server):
    global command_item
    loadOrdersJson(server)


def on_player_joined(server, player, info):
    flag = True
    if orders.check_player(player):
        flag = False
        if orders.check_order_on_player_join(player):
            time.sleep(3)   # 延迟 3s 后再提示，防止更多进服消息混杂而看不到提示
            server.tell(player, "§6[MCDRpost] §e您有待查收的快件~ 命令 §7!!po rl §e查看详情")
            server.execute(f'execute at {player} run playsound minecraft:entity.arrow.hit_player player {player}')
    if flag:
        orders.add_player(player)
        server.logger.info(f'已登记玩家 {player}')
        orders.save_to_json(server.logger)
