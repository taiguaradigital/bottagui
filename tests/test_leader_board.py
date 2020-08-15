import unittest
from pyiqoptionapi import IQOption
import logging
import time


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
# 579121
email = "cayem28791@mail2paste.com"
password = "testerforapi2020"


class TestLeaderBoard(unittest.TestCase):

    def test_leader_board(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        self.assertEqual(iq_api.check_connect(), True)
        data = []
        last = 10000
        step = 10000
        init = 1
        for i in range(10):
            data.append(iq_api.get_leader_board('Worldwide', init, last, 0))
            init += step
            last += step
            self.assertTrue(type(data[i]) is dict)
            print(data[i])
            time.sleep(1)
        print(data)
        for i in range(10):
            for d in data[i]['result']['positional']:
                print('positional {} -> {}'.format(d, data[i]['result']['positional'][d]))
        iq_api.close_connect()

