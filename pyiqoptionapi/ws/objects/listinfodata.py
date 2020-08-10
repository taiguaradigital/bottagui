# -*- coding: utf-8 -*-
from pyiqoptionapi.ws.objects.base import Base
from threading import RLock


class ListInfoData(Base):
    """Class for IQ Option Candles websocket object."""

    def __init__(self):
        super(ListInfoData, self).__init__()
        self.__name = "listInfoData"
        self.listinfodata_dict = {}
        self._lock = RLock()

    def set(self, win, game_state, id_number):
        with self._lock:
            self.listinfodata_dict[id_number] = {"win": win, "game_state": game_state }

    def delete(self, id_number):
        with self._lock:
            del self.listinfodata_dict[id_number]

    def get(self, id_number):
        with self._lock:
            return self.listinfodata_dict[id_number]
