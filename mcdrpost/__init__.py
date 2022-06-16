# -*- coding: utf-8 -*-

import json
import os
import time

from mcdreforged.api.all import *

from mcdrpost.OrdersData import orders
from mcdrpost.utils import (_tr, can_command_item, execute_replace_offhand,
                            format_time, get_offhand_item)

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
        logger.info(_tr('no_datafile'))
        if not os.path.exists(OrderJsonDirectory):
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
            RText(Prefix+' ls orders', RColor.gray).c(RAction.suggest_command, "!!po ls orders").h(_tr('hover')),RText(f'{_tr("help.hint_ls_orders")}\n')
        )
    if source.has_permission_higher_than(2):
        # admin以上权限的添加信息
        msgs_on_admin = RTextList(
            RText(Prefix+_tr('help.player_add'), RColor.gray).c(RAction.suggest_command, "!!po player add ").h(_tr('hover')),RText(f'{_tr("help.hint_player_add")}\n'),
            RText(Prefix+_tr('help.player_remove'), RColor.gray).c(RAction.suggest_command, "!!po player remove ").h(_tr('hover')),RText(f'{_tr("help.hint_player_remove")}\n'),
        )
    
    source.reply(
        RTextList(
            RText('--------- §3MCDRpost §r---------\n'),
            RText(f'{_tr("desc")}\n'),
            RText(f'{_tr("help.title")}\n'),
            RText(Prefix, RColor.gray).c(RAction.suggest_command, "!!po").h(_tr('hover')),RText(f' | {_tr("help.hint_help")}\n'),
            RText(Prefix+_tr('help.p'), RColor.gray).c(RAction.suggest_command, "!!po p ").h(_tr('hover')),RText(f'{_tr("help.hint_p")}\n'),
            RText(Prefix+' rl', RColor.gray).c(RAction.suggest_command, "!!po rl").h(_tr('hover')),RText(f'{_tr("help.hint_rl")}\n'),
            RText(Prefix+_tr('help.r'), RColor.gray).c(RAction.suggest_command, "!!po r ").h(_tr('hover')),RText(f'{_tr("help.hint_r")}\n'),
            RText(Prefix+' pl', RColor.gray).c(RAction.suggest_command, "!!po pl").h(_tr('hover')),RText(f'{_tr("help.hint_pl")}\n'),
            RText(Prefix+_tr('help.c'), RColor.gray).c(RAction.suggest_command, "!!po c ").h(_tr('hover')),RText(f'{_tr("help.hint_c")}\n'),
            RText(Prefix+' ls players', RColor.gray).c(RAction.suggest_command, "!!po ls players").h(_tr('hover')),RText(f'{_tr("help.hint_ls_players")}\n'),
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
        server.tell(player, _tr('clear_offhand'))
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

    if not infomsg: infomsg = _tr('no_comment')
    if not orders.check_storage(sender):
        src.reply(_tr('at_max_storage', MaxStorageNum))
        return
    if not orders.check_player(receiver):
        src.reply(_tr('no_receiver', receiver))
        return
    if sender == receiver:
        src.reply(_tr('same_person'))
        return
    if not itemjson:
        src.reply(_tr('check_offhand'))
        return
    else:
        item_tag = itemjson.get('tag', '')
        item = str(itemjson.get('id')) + \
            (json.dumps(item_tag, ensure_ascii=False) if len(item_tag) > 0 else '')+ ' ' + \
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
        src.reply(_tr('reply_success_post'))
        server.execute(f'execute at {sender} run playsound minecraft:entity.arrow.hit_player player {sender}')
        server.tell(receiver, _tr('hint_receive', postId))
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
        src.reply(_tr('no_porders'))
        return
    listmsg = '''==========================================
    {0}
    {1}
    -------------------------------------------
    {2}
==========================================='''.format(_tr('list_porders_title'), listmsg, _tr('hint_cancel'))
    src.reply(listmsg)


def receive_item(src: InfoCommandSource, orderid):
    # !!po c orderid
    player = src.get_info().player
    server = src.get_server()
    try:
        if not player == orders.orders[str(orderid)]['receiver']:
            src.reply(_tr('not_receiver'))
            return False
    except KeyError:
        src.reply(_tr('uncheck_orderid'))
        return False
    if not get_item(server, player, orderid):
        return False
    src.reply(_tr('receive_success', orderid))
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
        src.reply(_tr('no_rorders'))
        return
    listmsg = '''==========================================
    {0}
    {1}
    -------------------------------------------
    {2}
==========================================='''.format(_tr('list_rorders_title'), listmsg, _tr('hint_order_receive'))
    src.reply(listmsg)


def cancel_order(src: InfoCommandSource, orderid):
    # !!po c orderid
    player = src.get_info().player
    server = src.get_server()
    try:
        if not player == orders.orders[str(orderid)]['sender']:
            src.reply(_tr('not_sender'))
            return False
    except KeyError:
        src.reply(_tr('uncheck_orderid'))
        return False
    if not get_item(server, player, orderid):
        return False
    src.reply(_tr('cancel_success', orderid))
    regular_save_order_json(server.logger)


def list_players(src: InfoCommandSource):
    # !!po ls players
    src.reply(_tr('list_player_title') + str(orders.get_players()))


def list_orders(src: InfoCommandSource):
    # !!po ls orders
    listmsg = ''
    for orderid in orders.ids:
        order = orders.orders.get(str(orderid))
        if not order:
            continue
        listmsg = listmsg+str(orderid)+'  | '+order.get('sender')+'  | '+order.get('receiver')+'  | '+order.get('time')+'  | '+order.get('info')+'\n    '
    if listmsg == '':
        src.reply(_tr('no_orders'))
        return
    listmsg = '''==========================================
    {0}
    {1}
==========================================='''.format(_tr('list_orders_title'), listmsg)
    src.reply(listmsg)


def add_player_to_list(src: InfoCommandSource, player_id: str):
    if orders.check_player(player_id):
        src.reply(_tr('has_player'))
        return
    orders.add_player(player_id)
    src.reply(_tr('login_success', player_id))
    src.get_server().logger.info(_tr('login_log', player_id))
    orders.save_to_json(src.get_server().logger)


def remove_player_in_list(src: InfoCommandSource, player_id: str):
    if not orders.check_player(player_id):
        src.reply(_tr('cannot_del_player'))
        return
    orders.players.remove(player_id)
    src.reply(_tr('del_player_success', player_id))
    src.get_server().logger.info(_tr('del_player_log', player_id))
    orders.save_to_json(src.get_server().logger)



def register_command(server: PluginServerInterface):
    def required_errmsg(src: CommandSource, id: int):
        if id == 1:
            src.reply(_tr('only_for_player'))
        elif id == 2:
            src.reply(_tr('no_permission'))

    server.register_command(
        Literal(Prefix).
        runs(print_help_message).
        then(
            Literal('p').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            runs(lambda src: src.reply(_tr('no_input_receiver'))).
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
            runs(lambda src: src.reply(_tr('no_input_rorderid'))).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_receiver(src.get_info().player)).
                runs(lambda src, ctx: receive_item(src, ctx['orderid']))
            )
        ).
        then(
            Literal('rl').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            runs(list_inbox)
        ).
        then(
            Literal('c').requires(lambda src: src.is_player).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 1), handled=True).
            runs(lambda src: src.reply(_tr('no_input_corderid'))).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_sender(src.get_info().player)).
                runs(lambda src, ctx: cancel_order(src, ctx['orderid']))
            )
        ).
        then(
            Literal('ls').requires(lambda src: src.has_permission_higher_than(0)).
            on_error(RequirementNotMet, lambda src: required_errmsg(src, 2), handled=True).
            runs(lambda src: src.reply(_tr('command_incomplete'))).
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
            runs(lambda src: src.reply(_tr('command_incomplete'))).
            then(
                Literal('add').
                runs(lambda src: src.reply(_tr('command_incomplete'))).
                then(
                    Text('player_id').runs(lambda src, ctx: add_player_to_list(src, ctx['player_id']))
                )
            ).
            then(
                Literal('remove').
                runs(lambda src: src.reply(_tr('command_incomplete'))).
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
            server.tell(player, _tr('wait_for_receive'))
            server.execute(f'execute at {player} run playsound minecraft:entity.arrow.hit_player player {player}')
    if flag:
        orders.add_player(player)
        server.logger.info(_tr('login_log', player))
        orders.save_to_json(server.logger)
