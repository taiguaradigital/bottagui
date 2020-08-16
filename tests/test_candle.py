import unittest
import os
from pyiqoptionapi import IQOption
import logging
import time
import datetime
from tests.config import *


class TestCandle(unittest.TestCase):
  
    def test_Candle(self):
        iq_api=IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        balance = iq_api.get_balance()
        self.assertTrue(type(balance) is float)
        print('balance: {}'.format(balance))
        iq_api.reset_practice_balance()
        self.assertEqual(iq_api.check_connect(), True)
        ALL_Asset = iq_api.get_all_open_time(('turbo',))
        if ALL_Asset["turbo"]["EURUSD"]["open"]:
            ACTIVES="EURUSD"
        else:
            ACTIVES="EURUSD-OTC"
        iq_api.get_candles(ACTIVES, 60, 1000, time.time())
        size = "all"
        iq_api.start_candles_stream(ACTIVES, size, 10)
        iq_api.get_realtime_candles(ACTIVES, size)
        iq_api.stop_candles_stream(ACTIVES, size)
        iq_api.close_connect()
