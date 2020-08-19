import unittest
from pyiqoptionapi import IQOption
import logging
import time
from collections import defaultdict
from tests.config import *


class TestLeaderBoard(unittest.TestCase):

    def test_leader_board(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        self.assertEqual(iq_api.check_connect(), True)
        time.sleep(1)
        near_traders = iq_api.get_leader_board(near_traders_count=100)

        print('___________________________ 100 Near Traders to this ranking account ______________________')
        for k, v in near_traders['near_traders'].items():
            print(' -> {} Name: {} - Profit: {} Country: {}'.format(k, v['user_name'], v['score'], v['flag']))
        time.sleep(1)
        top_ten_country = iq_api.get_top_ten_countries()
        self.assertTrue(len(top_ten_country) == 10)

        print('___________________________ Top 10 Countries Ranking  ______________________')
        for k, v in top_ten_country.items():
            print(' -> {} - {} Profit: {}'.format(k, v['country_name'], v['profit']))
        time.sleep(1)
        top_traders = iq_api.get_positional_ranking_traders(to_position=100000)
        self.assertIsNotNone(top_traders)

        print('___________________________ Top 100000 Worldwide Traders  ______________________')
        for k, v in top_traders.items():
            print(' -> {} Name: {} - Profit: {} Country: {}'.format(k, v['user_name'], v['score'], v['flag']))
        time.sleep(1)
        country = 'Brazil'
        top_traders_country = iq_api.get_positional_ranking_traders(country=country, to_position=50)

        print('___________________________ Top 50 Brazilians Traders  ______________________')

        print('Top {} Traders Country {} ->'.format(len(top_traders_country), country))
        for k, v in top_traders_country.items():
            print(' -> {} Name: {} - Profit: {} Country: {}'.format(k, v['user_name'], v['score'], v['flag']))

        iq_api.close_connect()
