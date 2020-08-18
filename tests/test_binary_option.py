import unittest
from pyiqoptionapi import IQOption
from tests.config import *
import time
import random


class TestBinaryOption(unittest.TestCase):
  
    def test_binary_option(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        iq_api.reset_practice_balance()
        self.assertEqual(iq_api.check_connect(), True)
        all_assets = iq_api.get_all_open_time()

        print("_______________________GET OPTION INFO___________________________")
        info_ok, option_info = iq_api.get_optioninfo(10)
        self.assertTrue(info_ok)
        self.assertIsNotNone(option_info)
        print(option_info)
        time.sleep(1)

        print("_______________________GET OPTION INFO v2___________________________")
        option_info2 = iq_api.get_optioninfo_v2(10)
        self.assertIsNotNone(option_info2)
        print(option_info2)
        time.sleep(1)

        print("_______________________BUY BINARY CALL 15 minutes expiration___________________________")
        if all_assets["binary"]["EURUSD"]["open"]:
            active = "EURUSD"
        else:
            active = "EURUSD-OTC"
        money = 1
        action_call = "call"
        expirations_mode = 15
        check_call, id_call = iq_api.buy(money, active, action_call, expirations_mode)
        self.assertTrue(check_call)
        self.assertTrue(type(id_call) is int)
        time.sleep(5)

        print("_______________________SELL BINARY CALL___________________________")
        self.assertTrue(iq_api.sell_option(id_call))

        if all_assets["turbo"]["EURUSD"]["open"]:
            active = "EURUSD"
        else:
            active = "EURUSD-OTC"
        expirations_mode = 1

        print("_______________________BUY TURBO PUT___________________________")
        action_call = "put"
        check_put, id_put = iq_api.buy(money, active, action_call, expirations_mode)
        self.assertTrue(check_put)
        self.assertTrue(type(id_put) is int)

        print("_______________________WAIT FOR RESULT TURBO PUT___________________________")
        result = iq_api.check_win_v3(id_put, expirations_mode)
        self.assertTrue(type(result) is float)
        print("RESULT FOR BUY TURBO PUT: {:.2f}".format(result))

        print("_______________________BINARY OPTION DETAIL___________________________")
        options_details = iq_api.get_binary_option_detail()
        print(options_details)

        all_profit = iq_api.get_all_profit()
        self.assertIsNotNone(all_profit)
        print(all_profit)

        print("_______________________BUY TURBO CALL___________________________")
        action_call = "call"
        check_call, id_call = iq_api.buy(money, active, action_call, expirations_mode)
        self.assertTrue(check_call)
        self.assertTrue(type(id_call) is int)

        print("_______________________WAIT FOR RESULT TURBO CALL___________________________")
        check = False
        start = time.time()
        limit = expirations_mode*60+10
        result = None
        while not check:
            if time.time()-start > limit:
                raise TimeoutError
            check, result = iq_api.check_win_v4(id_call)
            remaining = iq_api.get_remaning(expirations_mode)
            print("remaining: {}".format(remaining))
            time.sleep(1)
        print("RESULT FOR BUY TURBO  CALL: {:.2f}".format(result))

        print("_______________________MULTI BUY TURBO___________________________")
        actives = list()
        for k, v in all_assets['turbo'].items():
            if v['open']:
                actives.append(k)

        dirs = ['call', 'put']
        directions = list()
        prices = list()
        expirations = list()

        total_actives = len(actives)
        for _ in range(total_actives):
            directions.append(dirs[random.randrange(0, 1)])
            prices.append(random.randrange(1, 10))
            expirations.append(1)

        list_buys = iq_api.buy_multi(prices, actives, directions, expirations)

        time.sleep(1)

        for idx in range(total_actives):
            print('Buy {} at price {} of active {} on expiration {}'.format(directions[idx], prices[idx], actives[idx], expirations[idx]))

        self.assertTrue(type(list_buys) is list)

        print("_______________________ WAIT FOR RESULT MULTI BUY TURBO___________________________")

        start = time.time()
        limit = expirations_mode * 60 + 180

        results = list()
        count = 0
        tot = len(list_buys)

        self.assertTrue(total_actives == tot)

        while count < tot:
            if time.time() - start > limit:
                raise TimeoutError
            for idx in list_buys:
                if count == tot:
                    break
                if idx:
                    check, result = iq_api.check_win_v4(idx)
                    if check:
                        results.append(result)
                        count += 1
                else:
                    raise ValueError('this buy not ID')
                time.sleep(.2)

        self.assertTrue(len(results) == tot)

        for idx in range(len(results)):
            print("RESULT FOR BUY TURBO CALL {} (USD {:.2f} ): {:.2f}".format(actives[idx], prices[idx], results[idx]))
        iq_api.close_connect()
