# -*- coding: utf-8 -*-
"""Module for IQ Option Profile websocket object."""
from pyiqoptionapi.ws.objects.base import Base
from threading import RLock


class GameBetInfoData(Base):

    def __init__(self):
        super(GameBetInfoData, self).__init__()
        self._lock = RLock()
        self._lock_sucess = RLock()
        self.__isSuccessful = None
        self.__dict = {}

    def process_message(self, message):
        try:
            with self._lock_sucess:

                self.isSuccessful = message["msg"].get("isSuccessful")
            with self._lock:
                self.dict = message["msg"]
        except:
            pass

    @property
    def isSuccessful(self):
        with self._lock_sucess:
            return self.__isSuccessful

    @isSuccessful.setter
    def isSuccessful(self, isSuccessful):
        with self._lock_sucess:
            self.__isSuccessful = isSuccessful

    @property
    def dict(self):
        with self._lock:
            return self.__dict

    @dict.setter
    def dict(self, dict):
        with self._lock:
            self.__dict = dict
 

 