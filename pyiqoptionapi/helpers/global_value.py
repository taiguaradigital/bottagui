# -*- coding: utf-8 -*-
from threading import RLock


class Globals:

    def __init__(self):
        super(Globals, self).__init__()
        self._balance_id = None
        self._check_websocket_if_connect = None
        self._lock_connect = RLock()
        self._lock = RLock()
        self._ssid = None
        self._lock_ssid = RLock()
        self._check_websocket_if_error = None
        self._lock_error = RLock()
        self._websocket_error_reason = None
        self._lock_reason = RLock()
        self._ssl_Mutual_exclusion = False
        self._ssl_Mutual_exclusion_write = False
        self._lock_exc = RLock()

    @property
    def balance_id(self):
        with self._lock:
            return self._balance_id

    @balance_id.setter
    def balance_id(self, value):
        with self._lock:
            self._balance_id = value

    @property
    def check_websocket_if_connect(self):
        with self._lock_connect:
            return self._check_websocket_if_connect

    @check_websocket_if_connect.setter
    def check_websocket_if_connect(self, value):
        with self._lock_connect:
            self._check_websocket_if_connect = value
    
    @property
    def ssid(self):
        with self._lock_ssid:
            return self._ssid
    
    @ssid.setter
    def ssid(self, value):
        with self._lock_ssid:
            self._ssid = value
    
    @property
    def check_websocket_if_error(self):
        with self._lock_error:
            return self._check_websocket_if_error
    
    @check_websocket_if_error.setter
    def check_websocket_if_error(self, value):
        with self._lock_error:
            self._check_websocket_if_error = value
    
    @property
    def websocket_error_reason(self):
        with self._lock_reason:
            return self._websocket_error_reason

    @websocket_error_reason.setter
    def websocket_error_reason(self, value):
        with self._lock_reason:
            self._websocket_error_reason = value

    @property
    def ssl_Mutual_exclusion(self):
        with self._lock_exc:
            return self._ssl_Mutual_exclusion

    @ssl_Mutual_exclusion.setter
    def ssl_Mutual_exclusion(self, value):
        with self._lock_exc:
            self._ssl_Mutual_exclusion = value

    @property
    def ssl_Mutual_exclusion_write(self):
        with self._lock_exc:
            return self._ssl_Mutual_exclusion_write

    @ssl_Mutual_exclusion_write.setter
    def ssl_Mutual_exclusion_write(self, value):
        with self._lock_exc:
            self._ssl_Mutual_exclusion_write = value
