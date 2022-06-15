# -*- coding: utf-8 -*-
import json

from mcdreforged.utils.logger import MCDReforgedLogger

class OrdersData:
    def __init__(self):
        self.players = []
        self.ids = [0]
        self.orders = {}
    
    def load_json(self, path: str):
        try:
            with open(path) as f:
                orders_dict = json.load(f, encoding='utf8')
                self.players = orders_dict.get('players', [])
                self.ids = orders_dict.get('ids', [])
                self.orders = orders_dict
                self.orders.pop('players')
                self.orders.pop('ids')
        except:
            return
    
    def add_player(self, player: str):
        self.players.append(player)
    
    def get_players(self) -> list:
        return self.players
    
    def get_orderid_by_receiver(self, receiver: str) -> list:
        return [i for i in self.ids if self.orders.get(str(i), {}).get('receiver') == receiver]

    def get_orderid_by_sender(self, sender: str) -> list:
        return [i for i in self.ids if self.orders.get(str(i), {}).get('sender') == sender]

    def save_to_json(self, logger: MCDReforgedLogger, path: str):
        tmp_orders = self.orders.copy()
        tmp_orders['players'] = self.players
        tmp_orders['ids'] = self.ids
        try:
            with open(path, 'w+') as f:
                json.dump(tmp_orders, f, indent=2)
            logger.info("[MCDRpost] Saved OrderJsonFile")
        except:
            return


orders = OrdersData()