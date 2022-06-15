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