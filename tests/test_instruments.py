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
        print(all_assets)
        self.assertTrue(type(all_assets) is defaultdict)
        iq_api.update_actives()
        actives = iq_api.get_binary_option_detail()
        self.assertTrue(type(actives) is defaultdict)
        print(actives)
        profits = iq_api.get_all_profit()
        self.assertTrue(type(profits) is defaultdict)
        print(profits)
        duration = 1
        active = None
        type_active = 'digital'
        time.sleep(1)
        assets = all_assets
        count = 0
        time.sleep(.5)
        types = ['binary', 'turbo', 'digital']
        for type_ in types:
            for active in assets[type_]:
                if not assets[type_][active]['open']:
                    continue
                if count == limit:
                    break
                try:
                    strikes = iq_api.get_strike_list(active, duration)[1]
                    print('Strikes for {} ( {} ) -> {}'.format(active, type_, strikes))
                except IndexError:
                    continue
                else:
                    for strike in strikes:
                        print(' -> {} -> {}'.format(strike, strikes[strike]))
                finally:
                    count += 1
                    time.sleep(.2)
            count = 0
        time.sleep(1)
        for asset in assets.get(type_active):
            if assets[type_active][asset]['open']:
                active = asset
                break
        if active:
            iq_api.subscribe_strike_list(active, duration)
            strikes = iq_api.get_realtime_strike_list(active, duration)
            print('Strikes {} digital -> {}'.format(active, strikes))
            for strike in strikes:
                print(' -> {} -> {}'.format(strike, strikes[strike]))
            iq_api.unsubscribe_strike_list(active, duration)
        time.sleep(1)
        quites = iq_api.get_instrument_quites_generated_data(active, duration)
        print(quites)
        iq_api.close_connect()
