import unittest
from pyiqoptionapi import IQOption
import logging
import time
import threading
from config import *


logging.basicConfig(level=logging.INFO, format='%(asctime)s ( %(threadName)s ): %(message)s')

number_of_symbols = 20
time_run = 30


class TestMultiSymbolsBinary(unittest.TestCase):

    def process_deals(self, api, active):
        print("_____________subscribe_live_deal {}_______________".format(active))
        api.subscribe_live_deal_binary(active, True)
        start_t = time.time()
        total = 0
        while True:
            entrances = api.get_live_deal_binary(active)
            if not entrances:
                continue
            total_entrances = len(entrances)
            total += total_entrances
            print("__For_binary_option__ data size: " + str(total_entrances))
            for ind in range(total_entrances):
                print(entrances[ind])
            time.sleep(1)
            if time.time() - start_t > time_run:
                break
        api.unsubscribe_live_deal_binary(active)
        print("_____________unsubscribe_live_deal {}_______________".format(active))
        all_deals = api.get_all_deals_binary(active, True)
        tot_all = len(all_deals)
        self.assertEqual(tot_all, total)
        print('list of all deals ( {} )-> {}'.format(tot_all, all_deals))


    def test_binary_option(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        iq_api.reset_practice_balance()
        self.assertEqual(iq_api.check_connect(), True)
        all_assets = iq_api.get_all_open_time()
        type_active = "turbo"
        actives = []
        threads = []
        count = 0
        for active in all_assets[type_active]:
            if count == number_of_symbols:
                break
            if all_assets[type_active][active]["open"]:
                actives.append(active)
            count += 1
        for active in actives:
            th = threading.Thread(name=active, target=self.process_deals, args=(iq_api, active), daemon=True)
            threads.append(th)
        for thread in threads:
            thread.start()
            time.sleep(.2)
        for thread in threads:
            thread.join()
        iq_api.close_connect()
