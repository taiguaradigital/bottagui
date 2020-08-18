import unittest
from pyiqoptionapi import IQOption
import logging
from tests.config import *


class TestUsers(unittest.TestCase):

    def test_users(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        iq_api.change_balance("PRACTICE")
        self.assertEqual(iq_api.check_connect(), True)
        users = iq_api.get_leader_board('Worldwide', 1, 1, 0)
        user_data = iq_api.get_users_availability(users['positional']['1']['user_id'])
        print(user_data)
        user_datas = iq_api.request_leaderboard_userinfo_deals_client(users['positional']['1']['user_id'],
                                                                      users['positional']['1']['flag'])
        self.assertTrue(type(user_datas) is dict)
        print(user_datas)
        self.assertTrue(type(iq_api.get_user_profile_client(users['positional']['1']['user_id'])) is dict)
        iq_api.close_connect()
