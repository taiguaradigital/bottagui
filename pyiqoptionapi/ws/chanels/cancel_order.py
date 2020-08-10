# -*- coding: utf-8 -*-
from pyiqoptionapi.ws.chanels.base import Base


class Cancel_order(Base):

    name = "sendMessage"

    def __call__(self, order_id):
        data = {
                "name": "cancel-order",
                "version": "1.0",
                "body": {
                            "order_id": int(order_id)
                         }
                }
        self.send_websocket_request(self.name, data)
