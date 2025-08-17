# -*- coding: utf-8 -*-
import json

from mcdreforged.api.types import MCDReforgedLogger

class OrdersData:
    def __init__(self):
        self.players = []
        self.ids = []
        self.orders = {}
        self.max_storage_num = 5
        self.json_file_path = ''
    
    def set_max_storage_num(self, num: int):
        self.max_storage_num = num

    def set_json_path(self, path: str):
        self.json_file_path = path

    def load_json(self):
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                orders_dict = json.load(f)
                self.players = orders_dict.get('players', [])
                self.ids = orders_dict.get('ids', [])
                self.orders = orders_dict
                self.orders.pop('players')
                self.orders.pop('ids')
        except Exception:
            return
    
    def add_player(self, player: str):
        self.players.append(player)
    
    def get_players(self) -> list:
        return self.players
    
    def get_orderid_by_receiver(self, receiver: str) -> list:
        return [i for i in self.ids if self.orders.get(str(i), {}).get('receiver') == receiver]

    def get_orderid_by_sender(self, sender: str) -> list:
        return [i for i in self.ids if self.orders.get(str(i), {}).get('sender') == sender]

    def get_next_id(self) -> str:
        nextid = 1
        self.ids.sort()
        for i, id in enumerate(self.ids):
            if i != id:
                nextid = i
                self.ids.append(nextid)
                return str(nextid)
        nextid = len(self.ids)
        self.ids.append(nextid)
        return str(nextid)

    def check_player(self, player: str) -> bool:
        return player in self.players

    def check_storage(self, player: str) -> bool:
        num = 0
        if self.max_storage_num < 0:
            return True
        for orderid in self.ids:
            order = self.orders.get(str(orderid), -1)
            if order == -1: continue
            if order.get('sender') == player:
                num += 1
                if num >= self.max_storage_num:
                    return False
        return True

    def check_order_on_player_join(self, player: str) -> bool:
        for orderid in orders.ids:
            order = self.orders.get(str(orderid), -1)
            if order == -1: continue
            if order.get('receiver') == player:
                return True
        return False

    def del_order(self, logger: MCDReforgedLogger, id):
        try:
            self.orders.pop(str(id))
            self.ids.remove(int(id))
            return True
        except Exception:
            logger.info("Error occurred during delete one PostOrder")
            return False

    def save_to_json(self, logger: MCDReforgedLogger):
        tmp_orders = self.orders.copy()
        tmp_orders['players'] = self.players
        tmp_orders['ids'] = self.ids
        try:
            with open(self.json_file_path, 'w+', encoding='utf-8') as f:
                json.dump(tmp_orders, f, indent=2, ensure_ascii=False)
            logger.info("Saved OrderJsonFile")
        except:
            return


orders = OrdersData()