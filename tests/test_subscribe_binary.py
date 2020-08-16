import unittest
from pyiqoptionapi import IQOption
import logging
import time
from threading import Thread
from tests.config import *


class TestSubscribeBinaryOption(unittest.TestCase):

    def test_options(self):
        self.iq_api = IQOption(email, password)
        self.iq_api.connect()
        self.iq_api.change_balance("PRACTICE")
        self.iq_api.reset_practice_balance()
        self.assertEqual(self.iq_api.check_connect(), True)
        all_assets = self.iq_api.get_all_open_time()
        if all_assets["turbo"]["EURUSD"]["open"]:
            active_turbo = "EURUSD"
        else:
            active_turbo = "EURUSD-OTC"
        if all_assets["binary"]["EURUSD"]["open"]:
            active_binary = "EURUSD"
        else:
            active_binary = "EURUSD-OTC"
        tht = Thread(target=self.turbo_option, args=(active_turbo,), daemon=True)
        tht.start()
        thb = Thread(target=self.binary_option, args=(active_binary,), daemon=True)
        thb.start()
        tht.join()
        thb.join()
        self.iq_api.close_connect()
        
    def turbo_option(self, active):

        self.iq_api.subscribe_live_deal_binary(active, True)
        start_t = time.time()
        while True:
            entrances = self.iq_api.get_live_deal_binary(active)
            if time.time() - start_t > 30:
                raise TimeoutError
            if entrances:
                print("__For_turbo_option__ data size: " + str(len(entrances)))
                for entrance in entrances:
                    print(entrance)
                break
        self.iq_api.unsubscribe_live_deal_binary(active, True)
        print("_____________unsubscribe_live_deal_______________")
        all_deals = self.iq_api.get_all_deals_binary(active, True)
        tot_all = len(all_deals)
        print('list of all deals ( {} ) turbo -> {}'.format(tot_all, all_deals))

    def binary_option(self, active):
        self.iq_api.subscribe_live_deal_binary(active, False)
        start_t = time.time()
        while True:
            entrances = self.iq_api.get_live_deal_binary(active, False)
            if time.time() - start_t > 60:
                raise TimeoutError
            if entrances:
                print("__For_binary_option__ data size: " + str(len(entrances)))
                for entrance in entrances:
                    print(entrance)
                break
        self.iq_api.unsubscribe_live_deal_binary(active, False)
        print("_____________unscribe_live_deal_______________")
        all_deals = self.iq_api.get_all_deals_binary(active, False)
        tot_all = len(all_deals)
        print('list of all deals ( {} ) binary -> {}'.format(tot_all, all_deals))
