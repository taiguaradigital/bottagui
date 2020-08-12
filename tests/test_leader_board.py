import unittest
from pyiqoptionapi import IQOption
import logging


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
        self.assertTrue(type(iq_api.get_leader_board('Worldwide', 1, 10000, 0)) is dict)
