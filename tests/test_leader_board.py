import unittest
from pyiqoptionapi import IQOption
import logging
import time
from collections import defaultdict


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
        time.sleep(1)
        near_trades = iq_api.get_leader_board(near_traders_count=100)
        print('100 Near Traders to this ranking account -> {}'.format(near_trades))
        self.assertTrue(len(near_trades['near_traders']) >= 100)
        time.sleep(1)
        top_ten_country = iq_api.get_top_ten_countries()
        self.assertTrue(len(top_ten_country) == 10)
        print('Top Ten Countries -> {}'.format(top_ten_country))
        time.sleep(1)
        country = 'Brazil'
        top_traders_country = iq_api.get_positional_ranking_traders(country=country, to_position=50)
        print('Top {} Traders Country {} ->'.format(len(top_traders_country), country))
        for k, v in top_traders_country.items():
            print(' -> {} Name: {} - Profit: {} Country: {}'.format(k, v['user_name'], v['score'], v['flag']))
        top_traders = iq_api.get_positional_ranking_traders(to_position=100000)
        print('Top {} Traders ->  {}'.format(len(top_traders), top_traders))
        for k, v in top_traders_country.items():
            print(' -> {} Name: {} - Profit: {} Country: {}'.format(k, v['user_name'], v['score'], v['flag']))
        iq_api.close_connect()
