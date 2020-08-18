"""
    Copyright (C) 2019-2020 Deibson Carvalho (deibsoncarvalho)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

from pyiqoptionapi.ws.client import WebsocketClient
from .ssid import Ssid
from .get_balance import GetBalance
from .subscribe import (SubscribeLiveDeal,
                        SubscribeCommissionChanged,
                        SubscribeInstrumentQuitesGenerated,
                        SubscribeTopAssetsUpdated,
                        Subscribe,
                        SubscribeCandles)
from .unsubscribe import (Unsubscribe,
                          UnscribeLiveDeal,
                          UnsubscribeCandles,
                          UnsubscribeCommissionChanged,
                          UnsubscribeInstrumentQuitesGenerated,
                          UnsubscribeTopAssetsUpdated)

from .setactives import SetActives

from pyiqoptionapi.ws.chanels.candles import GetCandles
from pyiqoptionapi.ws.chanels.buyv2 import Buyv2
from pyiqoptionapi.ws.chanels.buyv3 import *
from pyiqoptionapi.ws.chanels.user import *
from pyiqoptionapi.ws.chanels.api_game_betinfo import GameBetInfo
from pyiqoptionapi.ws.chanels.instruments import Get_instruments
from pyiqoptionapi.ws.chanels.get_financial_information import GetFinancialInformation
from pyiqoptionapi.ws.chanels.strike_list import StrikeList
from pyiqoptionapi.ws.chanels.leaderboard import LeaderBoard

from pyiqoptionapi.ws.chanels.traders_mood import Traders_mood_subscribe
from pyiqoptionapi.ws.chanels.traders_mood import Traders_mood_unsubscribe
from pyiqoptionapi.ws.chanels.buy_place_order_temp import Buy_place_order_temp
from pyiqoptionapi.ws.chanels.get_order import Get_order
from pyiqoptionapi.ws.chanels.get_deferred_orders import GetDeferredOrders
from pyiqoptionapi.ws.chanels.get_positions import *

from pyiqoptionapi.ws.chanels.get_available_leverages import Get_available_leverages
from pyiqoptionapi.ws.chanels.cancel_order import Cancel_order
from pyiqoptionapi.ws.chanels.close_position import Close_position
from pyiqoptionapi.ws.chanels.get_overnight_fee import Get_overnight_fee
from pyiqoptionapi.ws.chanels.heartbeat import Heartbeat

from pyiqoptionapi.ws.chanels.digital_option import *
from pyiqoptionapi.ws.chanels.api_game_getoptions import *
from pyiqoptionapi.ws.chanels.sell_option import SellOption
from pyiqoptionapi.ws.chanels.change_tpsl import Change_Tpsl
from pyiqoptionapi.ws.chanels.change_auto_margin_call import ChangeAutoMarginCall

from pyiqoptionapi.ws.objects.timesync import TimeSync
from pyiqoptionapi.ws.objects.profile import Profile
from pyiqoptionapi.ws.objects.candles import Candles
from pyiqoptionapi.ws.objects.listinfodata import ListInfoData
from pyiqoptionapi.ws.objects.betinfo import GameBetInfoData

__all__ = ['Ssid', 'GetBalance', 'SubscribeLiveDeal', 'SubscribeCommissionChanged', 'SubscribeInstrumentQuitesGenerated',
           'SubscribeTopAssetsUpdated', 'Subscribe', 'SubscribeCandles', 'Unsubscribe', 'UnscribeLiveDeal',
           'UnsubscribeCandles', 'UnsubscribeCommissionChanged', 'UnsubscribeInstrumentQuitesGenerated',
           'UnsubscribeTopAssetsUpdated', 'SetActives']
