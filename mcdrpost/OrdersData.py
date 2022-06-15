# -*- coding: utf-8 -*-

class OrdersData:
    def __init__(self):
        self.players = []
        self.ids = [0]
    
    def load_json(self, path: str):
        try:
            with open(path) as f:
                orders_dict = json.load(f, encoding='utf8')
                self.players = orders_dict.get('players', [])
                self.players = orders_dict.get('ids', [])
        except:
            return
    
orders = OrdersData()