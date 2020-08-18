import unittest
from pyiqoptionapi import IQOption
import logging
import time
import asyncio
from tests.config import *


class TestTradersDetails(unittest.TestCase):

    def test_traders_details(self):
        iq_api = IQOption(email, password)
        iq_api.connect()
        self.assertEqual(iq_api.check_connect(), True)
        iq_api.change_balance("PRACTICE")
        all_assets = iq_api.get_all_open_time()
        if all_assets["digital"]["EURUSD"]["open"]:
            active = "EURUSD"
        else:
            active = "EURUSD-OTC"
        print("_____________subscribe_live_deal digital_______________")
        iq_api.subscribe_live_deal_digital(active)
        start_t = time.time()
        start = True
        limit = 30
        count = 0
        while count < limit:
            entrances = iq_api.get_live_deal_digital(active)
            if entrances:
                for entrance in entrances:
                    print("_______ DEAL _______")
                    print(entrance)
                    user_id = entrance["user_id"]
                    country_id = entrance["country_id"]
                    print("_______get_user_profile_client__________")
                    pro_data = iq_api.get_user_profile_client(user_id)
                    print(pro_data)
                    print("___________request_leaderboard_userinfo_deals_client______")
                    user_data = iq_api.request_leaderboard_userinfo_deals_client(user_id, country_id)
                    print(user_data)
                    worldwide = user_data["result"]["entries_by_country"]["0"]["position"]
                    profit = user_data["result"]["entries_by_country"]["0"]["score"]
                    print("\n")
                    print("user_name:" + pro_data["user_name"])
                    print("This week worldwide:" + str(worldwide))
                    print("This week's gross profit:" + str(profit))
                    print("\n\n")

                    print("___________get_users_availability____________")
                    print(iq_api.get_users_availability(user_id))
                    print("\n\n")
                    count += 1
                    time.sleep(1)
                time.sleep(1)
        print("_____________unsubscribe_live_deal digital_______________")
        iq_api.subscribe_live_deal_digital(active)
        iq_api.close_connect()
