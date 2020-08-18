import unittest
from pyiqoptionapi import IQOption
import logging
import time
import asyncio
from tests.config import *


class TestDigitalOption(unittest.TestCase):

    def test_digital_option(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        self.assertEqual(iq_api.check_connect(), True)
        iq_api.change_balance("PRACTICE")
        all_assets = iq_api.get_all_open_time()
        if all_assets["digital"]["EURUSD"]["open"]:
            actives = "EURUSD"
        else:
            actives = "EURUSD-OTC"
        money = 1
        action_call = "call"
        expirations_mode = 1
        check_call, id_call = iq_api.buy_digital_spot(actives, money, action_call, expirations_mode)
        self.assertTrue(check_call)
        self.assertTrue(type(id_call) is int)
        start = time.time()
        iq_api.subscribe_strike_list(actives, expirations_mode)
        limit = expirations_mode*60+60
        while not iq_api.check_win_digital_v2(id_call)[0]:
            if time.time()-start > limit:
                raise TimeoutError
            spot = iq_api.get_digital_spot_profit_after_sale(id_call)
            print('Current Spot After Sale: {}'.format(spot))
            time.sleep(1)
        iq_api.unsubscribe_strike_list(actives, expirations_mode)
        result = iq_api.check_win_digital_v2(id_call)[1]
        self.assertTrue(type(result) is float)
        print('Result: {}'.format(result))
        action_call = "put"
        check_put, id_put = iq_api.buy_digital_spot(actives, money, action_call, expirations_mode)
        self.assertTrue(check_put)
        self.assertTrue(type(id_put) is int)
        self.assertTrue(iq_api.close_digital_option(id_put))
        asyncio.run(iq_api.check_win_digital_v3(id_put))
        iq_api.get_digital_position(id_put)
        iq_api.check_win_digital(id_put)
        limit = 5
        duration = 1
        count = 0
        for active in all_assets['digital']:
            if not all_assets['digital'][active]['open']:
                continue
            if count == limit:
                break
            try:
                strikes = iq_api.get_strike_list(active, duration)[1]
                print('Strikes for {} ( {} ) -> {}'.format(active, "digital", strikes))
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
        type_asset = 'digital'
        for active in all_assets[type_asset]:
            if all_assets[type_asset][active]['open']:
                iq_api.subscribe_strike_list(active, duration)
                time.sleep(.2)
                current_profit = iq_api.get_digital_current_profit(active, duration)
                print('current profit for {} ( {} ) -> {}'.format(active, type_asset, current_profit))
                time.sleep(.2)
                strikes = iq_api.get_realtime_strike_list(active, duration)
                print('Strikes {} digital -> {}'.format(active, strikes))
                for strike in strikes:
                    print(' -> {} -> {}'.format(strike, strikes[strike]))
                time.sleep(1)
                quites = iq_api.get_instrument_quites_generated_data(active, duration)
                print('quites for {} ( {} ) -> {}'.format(active, type_asset, quites))
                iq_api.unsubscribe_strike_list(active, duration)
                break
        iq_api.close_connect()
