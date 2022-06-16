# -*- coding: utf-8 -*-
import time

from mcdreforged.plugin.server_interface import PluginServerInterface

def format_time():
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def get_offhand_item(server: PluginServerInterface, player):
    MCDataAPI = server.get_plugin_instance('minecraft_data_api')
    
    try:
        offhandItem = None
        if server.is_rcon_running():
            offhandItemStr = server.rcon_query(f'data get entity {player} Inventory[{{Slot:-106b}}]')
            offhandItem = MCDataAPI.convert_minecraft_json(offhandItemStr)
        else:
            server.logger.info("Please config rcon of server correctly.")
            offhandItem = MCDataAPI.get_player_info(player, 'Inventory[{Slot:-106b}]')
            
        if type(offhandItem) == dict:
            return offhandItem
        else:
            return None
    except Exception as e:
        server.logger.info("Error occurred during getOffhandItem" + e.__class__.__name__)
        return None

def execute_replace_offhand(server: PluginServerInterface, player: str, item: str, command_item=-1):
    # command_item 是否可用item命令， -1为不可知，0为不可用（需要用replaceitem），1为可用
    try:
        if command_item == 1:
            server.execute(f'item replace entity {player} weapon.offhand with {item}')
        elif command_item == 0:
            server.execute(f'replaceitem entity {player} weapon.offhand {item}')
        else:
            server.execute(f'item replace entity {player} weapon.offhand with {item}')
            server.execute(f'replaceitem entity {player} weapon.offhand {item}')    
    except Exception as e:
        server.logger.warning(e)

def can_command_item(server: PluginServerInterface) -> int:
    # 判断是否可用item命令， -1为不可知，0为不可用（需要用replaceitem），1为可用
    # rcon发送help item replace，若可用item命令则会返回相应帮助信息(信息内包含item replace)
    try:
        if server.is_rcon_running():
            help_msg = server.rcon_query('help item replace')
            if 'item replace' in help_msg: return 1
            else: return 0
        else:
            return -1
    except Exception as e:
        server.logger.warning(e)
        return -1