import unittest
from pyiqoptionapi import IQOption
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')


#579121
email = "cayem28791@mail2paste.com"
password = "testerforapi2020"


class TestBinaryOption(unittest.TestCase):
  
    def test_binary_option(self):
        iq_api=IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        iq_api.reset_practice_balance()
        self.assertEqual(iq_api.check_connect(), True)
        all_assets=iq_api.get_all_open_time()
        if all_assets["turbo"]["EURUSD"]["open"]:
            active="EURUSD"
        else:
            active="EURUSD-OTC"
        Money=1
        ACTION_call="call"
        expirations_mode=1
        check_call, id_call = iq_api.buy(Money, active, ACTION_call, expirations_mode)
        self.assertTrue(check_call)
        self.assertTrue(type(id_call) is int)
        self.assertTrue(iq_api.sell_option(id_call))
        ACTION_call="put"
        check_put, id_put = iq_api.buy(Money, active, ACTION_call, expirations_mode)
        self.assertTrue(check_put)
        self.assertTrue(type(id_put) is int)
        self.assertTrue(iq_api.sell_option(id_put))
        iq_api.check_win_v3(id_put)
        iq_api.get_binary_option_detail()
        iq_api.get_all_profit()
        iq_api.get_optioninfo(10)
