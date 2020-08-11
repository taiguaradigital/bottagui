import unittest
from pyiqoptionapi import IQOption
import logging
import time
import asyncio

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

# 579121
email = "cayem28791@mail2paste.com"
password = "testerforapi2020"


class TestDigitalOption(unittest.TestCase):

    def test_binary_option(self):
        I_want_money = IQOption(email, password)
        I_want_money.connect()
        self.assertEqual(I_want_money.check_connect(), True)
        I_want_money.change_balance("PRACTICE")
        ALL_Asset = I_want_money.get_all_open_time()
        if ALL_Asset["digital"]["EURUSD"]["open"]:
            ACTIVES = "EURUSD"
        else:
            ACTIVES = "EURUSD-OTC"
        Money = 1
        ACTION_call = "call"
        expirations_mode = 1
        check_call, id_call = I_want_money.buy_digital_spot(ACTIVES, Money, ACTION_call, expirations_mode)
        self.assertTrue(check_call)
        self.assertTrue(type(id_call) is int)
        self.assertTrue(I_want_money.close_digital_option(id_call))
        ACTION_call = "put"
        check_put, id_put = I_want_money.buy_digital_spot(ACTIVES, Money, ACTION_call, expirations_mode)
        self.assertTrue(check_put)
        self.assertTrue(type(id_put) is int)
        self.assertTrue(I_want_money.close_digital_option(id_put))
        asyncio.run(I_want_money.check_win_digital_v3(id_put))
        I_want_money.get_digital_position(id_put)
        I_want_money.check_win_digital(id_put)
        I_want_money.subscribe_strike_list(ACTIVES, expirations_mode)
        data= False
        while not data:
            data = I_want_money.get_digital_current_profit(ACTIVES, expirations_mode)
            time.sleep(1)
        I_want_money.unsubscribe_strike_list(ACTIVES, expirations_mode)
