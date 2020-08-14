"""
    -*- coding: utf-8 -*-

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
from pyiqoptionapi.ws.objects.base import Base
from threading import RLock
from _collections import defaultdict, deque
import pyiqoptionapi.helpers.constants as OP_code
import logging
from functools import lru_cache


class LiveDeals(Base):

    def __init__(self):
        super(LiveDeals, self).__init__()
        self._lock_all = RLock()
        self._lock_queue = RLock()
        self._all_deals = defaultdict(list)
        self._queue_live_deals = defaultdict(deque)

    @staticmethod
    @lru_cache(maxsize=64)
    def __get_active_name(active_id) -> str:
        """Internal function for get active name by ID

        Retrieves string of active name.

        Args:
            active_id: (int) id of active

        Returns:
            A string  For example:  'EURUSD'

        Raises:
            IndexError: An error occurred accessing the dict of Actives ID.
        """
        actives = OP_code.ACTIVES
        try:
            return list(actives.keys())[list(actives.values()).index(active_id)]
        except IndexError:
            logging.error('get-active-name-by-id -> index error -> active_id: {}'.format(active_id))

    def get_all_deals(self, active) -> list:
        """Function to return all registered trades for the specified asset for the current session

        Returns a list containing a dict with the registered trade data.

        Args:
            active: (string) id of active

        Returns:
            A list of dict with keys: 'active_id', 'amount_enrolled', 'avatar', 'country_id',
            'created_at', 'direction', 'expiration', 'flag', 'is_big', 'name', 'option_id', 'option_type',
            'user_id', 'brand_id'.

            For example:

            [{'active_id': 1, 'amount_enrolled': 6.0, 'avatar': '', 'country_id': 205, 'created_at': 1597403952000,
            'direction': 'call', 'expiration': 1597404000000, 'flag': 'AE', 'is_big': False,
            'name': 'Obaid S. O. H. A.', 'option_id': 7190473575, 'option_type': 'turbo', 'user_id': 7262400,
            'brand_id': 1},
            {'active_id': 1, 'amount_enrolled': 35.0, 'avatar': '', 'country_id': 180,
            'created_at': 1597403952000, 'direction': 'call', 'expiration': 1597404000000, 'flag': 'ZA',
            'is_big': False, 'name': 'Ephraim G.', 'option_id': 7190473547, 'option_type': 'turbo', 'user_id': 12590610,
            'brand_id': 1}]

        Raises:
            KeyError: An error occurred accessing the dict of deals. Invalid active or not registed deals for
            current session
        """
        try:
            with self._lock_all:
                return self._all_deals[active]
        except KeyError:
            logging.error('asset {} invalid'.format(active))
            return []

    def get_live_deals(self, active, buffer) -> deque:
        """Function to return all registered trades for the specified asset for the current session

                Returns a deque containing a dict of live deals returned of IQ Option server

                Args:
                    active: (string) name of active
                    buffer: (int) number of return deals for call

                Returns:
                    A deque of dict with keys:

                    Binary or Turbo: 'active_id', 'amount_enrolled', 'avatar', 'country_id',
                    'created_at', 'direction', 'expiration', 'flag', 'is_big', 'name', 'option_id', 'option_type',
                    'user_id', 'brand_id'.

                    Digital: 'amount_enrolled','avatar','country_id','created_at', 'expiration_type','flag',
                    'instrument_active_id','instrument_dir', 'instrument_expiration','is_big','name','position_id',
                    'user_id','brand_id'.

                    For example:

                    Binary or Turbo:
                    ({'active_id': 1, 'amount_enrolled': 6.0, 'avatar': '', 'country_id': 205,
                    'created_at': 1597403952000, 'direction': 'call', 'expiration': 1597404000000, 'flag': 'AE',
                    'is_big': False,  'name': 'Obaid S. O. H. A.', 'option_id': 7190473575, 'option_type': 'turbo',
                    'user_id': 7262400, 'brand_id': 1})

                    Digital:
                    ({"amount_enrolled":6.0,"avatar":"","country_id":30,"created_at":1597413960301,
                    "expiration_type":"PT1M","flag":"BR","instrument_active_id":1,"instrument_dir":"put",
                    "instrument_expiration":1597414020000,"is_big":true,"name":"William O.","position_id":12004821753,
                    "user_id":76200274,"brand_id":1})

                Raises:
                    KeyError: An error occurred accessing the dict of deals. Invalid active or not registed deals for
                    current session
                """
        response = deque()
        try:
            total = len(self._queue_live_deals[active])
        except KeyError:
            logging.error('asset {} invalid'.format(active))
            return response
        if total == 0:
            return response
        for _ in range(buffer if total > buffer > 0 else total):
            with self._lock_queue:
                deal = self._queue_live_deals[active].pop()
            response.appendleft(deal)
            with self._lock_all:
                self._all_deals[active].append(deal)
        return response

    def set_live_deals(self, message):
        """ get new deals of websocket client """
        try:
            if 'option_type' in message.keys():
                # binary or turbo
                active_name = self.__get_active_name(message["active_id"])
            else:
                # digital
                active_name = self.__get_active_name(message["instrument_active_id"])
            with self._lock_queue:
                self._queue_live_deals[active_name].append(message)
        except KeyError:
            logging.error('set-live-deals -> invalid message -> {}'.format(message))
