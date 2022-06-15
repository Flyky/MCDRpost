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


def register_command(server: PluginServerInterface):
    server.register_command(
        Literal(Prefix).
        runs(print_help_message).
        then(
            Literal('p').requires(lambda src: src.isplayer).
            then(
                Text('receiver').suggests(orders.get_players).
                then(
                    GreedyText('comment').
                    runs(lambda src, ctx: post_item(src, ctx['receiver'], ctx['comment']))
                )
            )
        ).
        then(
            Literal('pl').requires(lambda src: src.isplayer).
            runs(list_outbox)
        ).
        then(
            Literal('r').requires(lambda src: src.isplayer).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_receiver(src.get_info().player)).
                runs(receive_item)
            )
        ).
        then(
            Literal('rl').requires(lambda src: src.isplayer).
            then(list_inbox)
        ).
        then(
            Literal('c').requires(lambda src: src.isplayer).
            then(
                Integer('orderid').
                suggests(lambda src: orders.get_orderid_by_sender(src.get_info().player)).
                runs(cancel_order)
            )
        ).
        then(
            Literal('ls').requires(lambda src: src.has_permission_higher_than(0)).
            then(
                Literal('players').runs()
            ).
            then(
                Literal('orders').requires(lambda src: src.has_permission_higher_than(1)).
                runs()
            )
        ).
        then(
            Literal('player').requires(lambda src: src.has_permission_higher_than(2)).
            then(
                Literal('add').then(
                    Text('player_name').runs()
                )
            ).
            then(
                Literal('remove').then(
                    Text('player_name').runs()
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