import unittest
from pyiqoptionapi import IQOption
import logging
import time
from _collections import defaultdict


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

# 579121
email = "cayem28791@mail2paste.com"
password = "testerforapi2020"

limit = 5


class TestInstruments(unittest.TestCase):

    def test_instruments_option(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        self.assertEqual(iq_api.check_connect(), True)
        iq_api.change_balance("PRACTICE")
        all_assets = iq_api.get_all_open_time()
        print('all assets -> {}'.format(all_assets))
        self.assertIsNotNone(all_assets)
        iq_api.update_actives()
        time.sleep(1)
        response = iq_api.get_actives_by_profit()
        self.assertIsNotNone(response)
        print(response)
        iq_api.close_connect()
