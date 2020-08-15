import unittest
from pyiqoptionapi import IQOption
import logging
from pyiqoptionapi.helpers import *


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
# 579121
email = "cayem28791@mail2paste.com"
password = "testerforapi2020"


class TestCountries(unittest.TestCase):

    def test_countries(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        country = Countries(iq_api)
        self.assertTrue(type(country.get_top_countries()) is dict)
        self.assertTrue(type(country.get_countries_names()) is list)
        self.assertTrue(type(country.get_country_id('Worldwide')) is int)
        iq_api.close_connect()
