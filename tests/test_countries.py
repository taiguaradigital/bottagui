import unittest
from pyiqoptionapi import IQOption
import logging
from pyiqoptionapi.helpers import *
from tests.config import *


class TestCountries(unittest.TestCase):

    def test_countries(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        country = Countries(iq_api)

        print("___________________ GET LIST COUNTRIES NAMES __________________________")
        countries = country.get_countries_names()
        self.assertTrue(type(countries) is list)
        for c in countries:
            print(c)

        country_id_w = country.get_country_id('Worldwide')
        self.assertTrue(type(country_id_w) is int)
        print('Wordwide ID: {}'.format(country_id_w))

        print("___________________ COUNTRY ID BY NAME __________________________")
        country_id_b = country.get_country_id('Brazil')
        self.assertTrue(type(country_id_b) is int)
        print('Brazil ID: {}'.format(country_id_b))

        print("___________________ COUNTRY ID BY SHORT NAME __________________________")
        country_id_b_s = country.get_country_id('BR')
        self.assertTrue(type(country_id_b_s) is int)
        print('BR ID: {}'.format(country_id_b_s))

        print("___________________ COUNTRY NAME BY ID __________________________")
        country_name = country.get_country_name(country_id_b)
        self.assertIsNotNone(country_name)
        print('ID {}: {}'.format(country_id_b, country_name))

        print("___________________ COUNTRY NAME BY SHORTNAME __________________________")
        country_name_2 = country.get_country_name("BR")
        self.assertIsNotNone(country_name_2)
        print('ID BR: {}'.format(country_name_2))

        iq_api.close_connect()
