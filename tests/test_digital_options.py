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
        iq_api = IQOption(email, password)
        iq_api.connect()
        self.assertEqual(iq_api.check_connect(), True)
        iq_api.change_balance("PRACTICE")
        all_assets = iq_api.get_all_open_time()
        if all_assets["digital"]["EURUSD"]["open"]:
            actives = "EURUSD"
        else:
            actives = "EURUSD-OTC"
        Money = 1
        action_call = "call"
        expirations_mode = 1
        check_call, id_call = iq_api.buy_digital_spot(actives, Money, action_call, expirations_mode)
        self.assertTrue(check_call)
        self.assertTrue(type(id_call) is int)
        self.assertTrue(iq_api.close_digital_option(id_call))
        action_call = "put"
        check_put, id_put = iq_api.buy_digital_spot(actives, Money, action_call, expirations_mode)
        self.assertTrue(check_put)
        self.assertTrue(type(id_put) is int)
        self.assertTrue(iq_api.close_digital_option(id_put))
        asyncio.run(iq_api.check_win_digital_v3(id_put))
        iq_api.get_digital_position(id_put)
        iq_api.check_win_digital(id_put)
        iq_api.subscribe_strike_list(actives, expirations_mode)
        data=False
        while not data:
            data = iq_api.get_digital_current_profit(actives, expirations_mode)
            time.sleep(1)
        iq_api.unsubscribe_strike_list(actives, expirations_mode)
        iq_api.close_connect()
