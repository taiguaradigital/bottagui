import unittest
from pyiqoptionapi import IQOption
import logging
import time


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

# 579121
email = "cayem28791@mail2paste.com"
password = "testerforapi2020"


class TestSubscribeDigitalOption(unittest.TestCase):

    def test_digital_option(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        self.assertEqual(iq_api.check_connect(), True)
        all_assets = iq_api.get_all_open_time()
        if all_assets["digital"]["EURUSD"]["open"]:
            active = "EURUSD"
        else:
            active = "EURUSD-OTC"
        print("_____________subscribe_live_deal digital_______________")
        iq_api.subscribe_live_deal_digital(active)
        start_t = time.time()
        while True:
            entrances = iq_api.get_live_deal_digital(active)
            if time.time() - start_t > 30:
                raise TimeoutError
            if entrances:
                print("__For_digital_option__ data size: " + str(len(entrances)))
                for entrance in entrances:
                    print(entrance)
                break
        print("_____________unsubscribe_live_deal digital_______________")
        iq_api.subscribe_live_deal_digital(active)
        iq_api.close_connect()
