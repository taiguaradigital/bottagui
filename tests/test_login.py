import unittest
import os
from pyiqoptionapi import IQOption
from tests.config import *
import time

class TestLogin(unittest.TestCase):
  
    def test_login(self):
        iq_api = IQOption(email, password)
        check, reason = iq_api.connect()
        self.assertTrue(check)
        self.assertIsNone(reason)
        print("________________________ CONNECTED ________________________________________")
        self.assertTrue(iq_api.check_connect())

        print("________________________ CHANGE REAL BALANCE  ________________________________________")
        res = iq_api.change_balance("REAL")
        self.assertTrue(res)
        time.sleep(3)

        print("________________________ CHANGE PRACTICE BALANCE  ________________________________________")
        res = iq_api.change_balance("PRACTICE")
        self.assertTrue(res)

        print("________________________ RESET PRACTICE BALANCE  ________________________________________")
        iq_api.reset_practice_balance()

        print("________________________ CLOSE CONNECTION  ________________________________________")
        iq_api.close_connect()
