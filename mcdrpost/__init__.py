# -*- coding: utf-8 -*-

import json
import time
import os

from mcdreforged.api.all import *
from mcdrpost.OrdersData import orders
from mcdrpost.utils import format_time, get_offhand_item

Prefix = '!!po'
MaxStorageNum = 5   # 最大存储订单量，设为-1则无限制
SaveDelay = 1
OrderJsonDirectory = './config/MCDRpost/'
OrderJsonFile = OrderJsonDirectory + 'PostOrders.json'

orders.set_json_path(OrderJsonFile)
orders.set_max_storage_num(MaxStorageNum)

def loadOrdersJson(logger: MCDReforgedLogger):
    if not os.path.isfile(OrderJsonFile):
        logger.info('[MCDRpost] 未找到数据文件，自动生成')
        os.makedirs(OrderJsonDirectory)
        with open(OrderJsonFile, 'w+') as f:
            f.write('{"players": [], "ids":[]}')
    orders.load_json(logger)


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
            RText(Prefix+' pl', RColor.gray).c(RAction.suggest_command, "!!po pl").h('点击写入聊天栏'),RText(' | 列出收件列表\n'),
            RText(Prefix+' c §6[<单号>]', RColor.gray).c(RAction.suggest_command, "!!po c ").h('点击写入聊天栏'),RText(' | 取消传送物品(收件人未收件前)，该单号物品退回到副手(取消前请将副手清空)\n'),
            RText(Prefix+' ls players', RColor.gray).c(RAction.suggest_command, "!!po ls players").h('点击写入聊天栏'),RText(' | 查看可被寄送的注册玩家列表\n'),
            msgs_on_helper,
            msgs_on_admin,
            RText('-----------------------')
        )
    )


def regularSaveOrderJson(logger: MCDReforgedLogger):
    if len(orders.ids) % SaveDelay == 0:
        orders.save_to_json(logger, OrderJsonFile)


def getItem(server, player, orderid):
    if not get_offhand_item(server, player):
        order = orders.orders.get(orderid, -1)
        server.execute(f'item replace entity {player} weapon.offhand with {str(order["item"])}')
        # server.execute(f'replaceitem entity {player} weapon.offhand {str(order["item"])}')
        server.execute(f'execute at {player} run playsound minecraft:entity.bat.takeoff player {player}')
        orders.del_order(server.logger, orderid)
        return True
    else:
        server.tell(player, '§e* 抱歉，请先将您的§6副手物品§e清空')
        return False


######### ########

def post_item(src: InfoCommandSource, receiver: str, infomsg=""):
    sender = src.get_info().player
    pass


def list_outbox(src: InfoCommandSource):
    pass


def receive_item(src: InfoCommandSource):
    pass


def list_inbox(src: InfoCommandSource):
    pass


def cancel_order(src: InfoCommandSource):
    pass


def add_player_to_list(src: InfoCommandSource, player_id: str):
    if orders.check_player(player_id):
        src.reply('§4* 该玩家已注册，请检查后再输入 \n§r使用 §7!!po ls players §r可以查看所有注册玩家列表')
        return
    orders.add_player(player_id)
    src.reply(f'§e[MCDRpost] §a成功注册玩家 §b{player_id} §a,使用 §7!!po ls players §a可以查看所有注册玩家列表')
    src.get_server().logger.info(f'[MCDRpost] 已登记玩家 {player_id}')
    orders.save_to_json(src.get_server().logger)


def remove_player_in_list(src: InfoCommandSource, player_id: str):
    if not orders.check_player(player_id):
        src.reply('§4* 该玩家未注册，无法进行删除 \n§r使用 §7!!po ls players §r可以查看所有注册玩家列表')
        return
    orders.players.remove(player_id)
    src.reply(f'§e[MCDRpost] §a成功删除玩家 §b{player_id} §a,使用 §7!!po ls players §a可以查看所有注册玩家列表')
    src.get_server().logger.info(f'[MCDRpost] 已删除登记玩家 {player_id}')
    orders.save_to_json(src.get_server().logger)



def register_command(server: PluginServerInterface):
    server.register_command(
        Literal(Prefix).
        runs(print_help_message).
        then(
            Literal('p').requires(lambda src: src.is_player).
            then(
                Text('receiver').suggests(orders.get_players).
                then(
                    GreedyText('comment').
                    runs(lambda src, ctx: post_item(src, ctx['receiver'], ctx['comment']))
                )
            )
        ).
        then(
            Literal('pl').requires(lambda src: src.is_player).
            runs(list_outbox)
        ).
        then(
            Literal('r').requires(lambda src: src.is_player).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_receiver(src.get_info().player)).
                runs(receive_item)
            )
        ).
        then(
            Literal('rl').requires(lambda src: src.is_player).
            then(list_inbox)
        ).
        then(
            Literal('c').requires(lambda src: src.is_player).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_sender(src.get_info().player)).
                runs(cancel_order)
            )
        ).
        then(
            Literal('ls').requires(lambda src: src.has_permission_higher_than(0)).
            then(
                Literal('players').runs(lambda: 1)
            ).
            then(
                Literal('orders').requires(lambda src: src.has_permission_higher_than(1)).
                runs(lambda: 1)
            )
        ).
        then(
            Literal('player').requires(lambda src: src.has_permission_higher_than(2)).
            then(
                Literal('add').then(
                    Text('player_id').runs(lambda src, ctx: add_player_to_list(src, ctx['player_id']))
                )
            ).
            then(
                Literal('remove').then(
                    Text('player_id').runs(lambda src, ctx: remove_player_in_list(src, ctx['player_id']))
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
        server.logger.info(f'[MCDRpost] 已登记玩家 {player}')
        orders.save_to_json(server.logger)
