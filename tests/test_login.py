import unittest
import os
from pyiqoptionapi import IQOption
from config import *


class TestLogin(unittest.TestCase):
  
    def test_login(self):
        iq_api=IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        iq_api.reset_practice_balance()
        self.assertEqual(iq_api.check_connect(), True)
        iq_api.close_connect()
