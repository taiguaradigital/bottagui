import unittest
import os
from pyiqoptionapi import IQOption


#579121
email = "cayem28791@mail2paste.com"
password = "testerforapi2020"


class TestLogin(unittest.TestCase):
  
    def test_login(self):
        I_want_money=IQOption(email,password)
        I_want_money.connect()
        I_want_money.change_balance("PRACTICE")
        I_want_money.reset_practice_balance()
        self.assertEqual(I_want_money.check_connect(), True)
