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
from pyiqoptionapi.api.api import IQOptionAPI as _api
import threading
import time
import logging
import operator
from collections import defaultdict
from collections import deque
from datetime import datetime, timedelta
from pyiqoptionapi.helpers import *
from .version import VERSION
from pyiqoptionapi.helpers.decorators import deprecated
from pyiqoptionapi.helpers.exceptions import *
from pyiqoptionapi.helpers.utils import nested_dict
from collections import OrderedDict
from .config import prepare
import math


__all__ = ['IQOption', ]


class IQOption:

    __version__ = VERSION
    __status__ = "production"

    def __init__(self, email, password, mode='INFO'):
        prepare(mode)
        self.__size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800,
                       3600, 7200, 14400, 28800, 43200, 86400, 604800, 2592000]
        self.__durations = [1, 5, 15]
        self.__lock_dur = threading.RLock()
        self.__lock_size = threading.RLock()
        self.email = email
        self.password = password
        self.suspend = 0.5
        self.thread = None
        self._lock_candle = threading.RLock()
        self._lock_subscribed_strike_list = threading.RLock()
        self.__subscribed_strike_list = []
        self.__subscribed_live_deal = []
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        # for digit
        self.get_digital_spot_profit_after_sale_data = nested_dict(2, int)
        self._lock_strike_list = threading.RLock()
        self.get_realtime_strike_list_temp_data = {}
        self.get_realtime_strike_list_temp_expiration = 0
        self.SESSION_HEADER = {
            "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          r"(KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"}
        self.SESSION_COOKIE = {}
        self.api = None

    @property
    def size(self):
        with self.__lock_size:
            return self.__size

    @property
    def durations(self):
        with self.__lock_dur:
            return self.__durations

    @property
    def actives(self):
        return self.api.actives

    @actives.setter
    def actives(self, actives):
        self.api.actives = actives

    def get_server_timestamp(self):
        return self.api.timesync.server_timestamp

    def re_subscribe_stream(self):
        try:
            with self._lock_candle:
                for ac in self.subscribe_candle:
                    sp = ac.split(",")
                    self.start_candles_one_stream(sp[0], sp[1])
        except Exception as e:
            logging.error('re-subscribe-stream -> {}'.format(e))

        try:
            with self._lock_candle:
                for ac in self.subscribe_candle_all_size:
                    self.start_candles_all_size_stream(ac)
        except Exception as e:
            logging.error('re-subscribe-stream -> {}'.format(e))

        try:
            with self._lock_candle:
                for ac in self.subscribe_mood:
                    self.start_mood_stream(ac)
        except Exception as e:
            logging.error('re-subscribe-stream -> {}'.format(e))

    def set_session(self, header, cookie):
        self.SESSION_HEADER = header
        self.SESSION_COOKIE = cookie

    @property
    def balance_id(self):
        return self.api.global_value.balance_id

    def connect(self) -> tuple:
        """ function for connect to server IQ Option

            return:
                Tuple with result (connected or not True / False) and Reason of not connected

                For Example:
                   Connected == (True, None)
                   Not Connected == (False, 'The balance ID is unavailable. Response timeout.')
        """
        self.api = _api("iqoption.com", self.email, self.password)
        check = False
        self.api.set_session(headers=self.SESSION_HEADER, cookies=self.SESSION_COOKIE)
        check, reason = self.api.connect()
        if check:
            self.re_subscribe_stream()
            start = time.time()
            while 1:
                if self.api.global_value.balance_id:
                    break
                if time.time() - start > 10:
                    return False, 'The balance ID is unavailable. Response timeout.'
                time.sleep(.1)
            self.position_change_all("subscribeMessage", self.api.global_value.balance_id)
            self.order_changed_all("subscribeMessage")
            self.api.setOptions(1, True)
            return True, None
        else:
            return False, reason

    def close_connect(self):
        """ function for close connect of server """
        try:
            self.api.close()
        except TypeError:
            pass

    def check_connect(self) -> bool:
        """ function for check if server is connected """
        if not self.api.global_value:
            return False
        return bool(self.api.global_value.check_websocket_if_connect)

    def get_all_actives(self):
        return self.actives

    def update_actives(self):
        self._get_all_binary_actives()
        self._instruments_input_all_in_actives()
        dicc = {}
        for lis in sorted(self.actives.items(), key=operator.itemgetter(1)):
            dicc[lis[0]] = lis[1]
        self.actives = dicc

    def get_name_by_active_id(self, active_id):
        info = self.get_financial_information(active_id)
        try:
            return info["msg"]["data"]["active"]["name"]
        except KeyError:
            return None

    def get_financial_information(self, active_id):
        with self.api.lock_financial_info:
            self.api.financial_information = None
        self.api.get_financial_information(active_id)
        start = time.time()
        while 1:
            if time.time() - start > 10:
                raise TimeoutError
            with self.api.lock_financial_info:
                if self.api.financial_information:
                    return self.api.financial_information

    def get_leader_board(self, *args, **kwargs) -> dict:
        """ Function to get strike list of turbo, binary and digital options

           Args / kwargs:
               country: (string) name of country; default: 'Worldwide'.
               from_position: (int) from position of trades of ranking; Default: 1
               to_position: (int) to position of trades of ranking; Default: 100
               near_traders_count: (int) number of trades near from ranking of current balance (account) logged;
               user_country: (int) country id; Default: 0
               near_traders_country_count: (int)
               top_country_count: (int)
               top_count: (int)
               top_type: (int)
               pooling_time: (int) Time for wait server response. Default is 300ms (5 minutes)
           return:
               A dict of data ranking

           For example:

                {'user_id': 76757666, 'country_id': 0, 'top_type': 2,
                'top_size': 306056, 'position': 306056, 'user_accounted_expiration_time': 0,
                'top': {'306056': {'user_id': 76757666, 'user_name': 'Test T.', 'score': 0.0, 'count': 0,
                'flag': 'BR'}},
                'positional': {'1': {'user_id': 16853304, 'user_name': 'Landon J.', 'score': 166105.12,
                'count': 378, 'flag': 'MX'},
                '2': {'user_id': 70036986, 'user_name': 'Yuri G. D.', 'score': 164773.70594, 'count': 100,
                 'flag': 'GY'},
                '3': {'user_id': 60673219, 'user_name': 'Miguel A. D. R. R.', 'score': 105171.71870499999,
                'count': 1418, 'flag': 'PE'}, '4': {'user_id': 70528083, 'user_name': 'Emma J.',
                'score': 104272.26503800003, 'count': 2977, 'flag': 'BR'}, '5': {'user_id': 37503537,
                'user_name': 'Aaron T.', 'score': 95231.62824200002, 'count': 2707, 'flag': 'KR'},
                '6': {'user_id': 22908162, 'user_name': 'Adrian C.', 'score': 91862.63630299999, 'count': 189,
                'flag': 'TH'},
                '7': {'user_id': 18021472, 'user_name': 'Riaan F.', 'score': 90754.83420999999, 'count': 5,
                'flag': 'ZA'},
                 '8': {'user_id': 75488497, 'user_name': 'Maria P.', 'score': 84165.703554, 'count': 71,
                 'flag': 'BR'},
                 '9': {'user_id': 63822006, 'user_name': 'Landon J.', 'score': 83230.25161299997, 'count': 1376,
                 'flag': 'CN'},
                 '10': {'user_id': 43124555, 'user_name': 'Nicola P.', 'score': 80801.75, 'count': 77, 'flag': 'CO'},
                 '11': {'user_id': 74054648, 'user_name': 'Shaun M.', 'score': 74006.34222399982, 'count': 467,
                 'flag': 'BM'},
                 '12': {'user_id': 67204771, 'user_name': 'Nguyen V. M.', 'score': 69622.63050099999,
                 'count': 204, 'flag': 'VN'},
                 '13': {'user_id': 3089081, 'user_name': 'Oliver R.', 'score': 67531.43063400002,
                 'count': 984, 'flag': 'BR'},
                 '14': {'user_id': 27546345, 'user_name': 'Ka L. K. I.', 'score': 64467.496652999995,
                 'count': 3788, 'flag': 'HK'},
                 '15': {'user_id': 45844787, 'user_name': 'Ava C.', 'score': 63811.88065100003, 'count': 65,
                 'flag': 'TH'},
                 '16': {'user_id': 76171561, 'user_name': 'Mateo K.', 'score': 60603.130252999996, 'count': 360,
                 'flag': 'BR'},
                 '17': {'user_id': 12700851, 'user_name': 'Antonio M. M.', 'score': 58949.28062600001,
                 'count': 146, 'flag': 'ES'},
                 '18': {'user_id': 13369320, 'user_name': 'Nelson K.', 'score': 58412.70622599999,
                 'count': 861, 'flag': 'BR'},
                 '19': {'user_id': 74393123, 'user_name': 'Marcos S.', 'score': 57744.04904700001,
                  'count': 607, 'flag': 'BR'},
                 '20': {'user_id': 13600742, 'user_name': 'shihabudeen s.', 'score': 55662.793837,
                 'count': 290, 'flag': 'SA'},
                  '21': {'user_id': 61721151, 'user_name': 'João P. N. R. D. S.', 'score': 55325.68611900001,
                  'count': 151, 'flag': 'BR'}, '22': {'user_id': 7201974, 'user_name': 'Jidveian O.',
                   'score': 53778.303679999946, 'count': 3317, 'flag': 'RO'}, '23': {'user_id': 73061677,
                   'user_name': 'Leonardo R.', 'score': 53540.43740300003, 'count': 411, 'flag': 'BR'},
                   '24': {'user_id': 40646705, 'user_name': 'Mohamed R. A.', 'score': 52916.57938400003,
                   'count': 856, 'flag': 'IN'}, '25': {'user_id': 18195609, 'user_name': 'Theewasit S.',
                   'score': 51055.65773099999, 'count': 425, 'flag': 'TH'}, '26': {'user_id': 49982163,
                   'user_name': 'Marlon C. D. S.', 'score': 50946.79124200001, 'count': 115, 'flag': 'BR'},
                   '27': {'user_id': 61571520, 'user_name': 'Arifi E. F. M. J.', 'score': 50922.301971999994,
                    'count': 118, 'flag': 'BR'}, '28': {'user_id': 58474778, 'user_name': 'Tse Y. L.',
                    'score': 50900.173237, 'count': 65, 'flag': 'AR'}, '29': {'user_id': 49768259,
                    'user_name': 'Jose W.', 'score': 50453.08858400001, 'count': 24, 'flag': 'GB'},
                    '30': {'user_id': 11279531, 'user_name': 'Beng C. C.', 'score': 49738.0, 'count': 187,
                    'flag': 'MY'},
                     '31': {'user_id': 76435817, 'user_name': 'saif a.', 'score': 49011.08086, 'count': 93,
                      'flag': 'IN'},
                     '32': {'user_id': 44885579, 'user_name': 'Thomas J.', 'score': 46268.943177, 'count': 79,
                     'flag': 'CR'},
                     '33': {'user_id': 32150521, 'user_name': 'Lincoln J.', 'score': 45951.23084899997,
                     'count': 406, 'flag': 'HK'},
                     '34': {'user_id': 12695474, 'user_name': 'Chase G.', 'score': 45018.26216600001,
                     'count': 82, 'flag': 'ZM'},
                      '35': {'user_id': 63648328, 'user_name': 'Hannah F.', 'score': 44705.45424699999,
                      'count': 619, 'flag': 'BR'},
                       '36': {'user_id': 53399459, 'user_name': 'Jeerasak T.', 'score': 44288.245914,
                       'count': 467, 'flag': 'TH'},
                       '37': {'user_id': 71996590, 'user_name': 'Yassar B. A. Z.', 'score': 43467.889462000014,
                       'count': 504, 'flag': 'AE'}, '38': {'user_id': 56120476, 'user_name': 'Rodrigo C. d. S.',
                       'score': 43206.89382299997, 'count': 137, 'flag': 'BR'}, '39': {'user_id': 76364737,
                       'user_name':
                        'paulo r.', 'score': 42710.574925, 'count': 156, 'flag': 'BR'}, '40': {'user_id': 75939247,
                        'user_name': 'Hannah A.', 'score': 42410.82707300001, 'count': 1479, 'flag': 'BR'},
                        '41': {'user_id': 47147518, 'user_name': 'Jayden D.', 'score': 40648.8, 'count': 287,
                        'flag': 'MX'},
                        '42': {'user_id': 71814235, 'user_name': 'Joshua G.', 'score': 39961.432432000016,
                        'count': 206, 'flag': 'CN'}, '43': {'user_id': 33847032, 'user_name': 'Leah K.',
                        'score': 39793.124370000005, 'count': 175, 'flag': 'BR'}, '44': {'user_id': 70832877,
                        'user_name': 'Kevin T.', 'score': 37666.63259900001, 'count': 301, 'flag': 'IN'},
                        '45': {'user_id': 49429309, 'user_name': 'Cameron S.', 'score': 37619.159774000014,
                        'count': 2670, 'flag': 'TH'}, '46': {'user_id': 6822849, 'user_name': 'vinicius r.',
                        'score': 37271.55617299999, 'count': 350, 'flag': 'BR'}, '47': {'user_id': 72578858,
                        'user_name': 'Saleh S.', 'score': 37107.23492700003, 'count': 2063, 'flag': 'ID'},
                        '48': {'user_id': 73026912, 'user_name': 'Isaac C.', 'score': 36003.986658999995,
                        'count': 578, 'flag': 'MX'}, '49': {'user_id': 59909268, 'user_name': 'Mateo S.',
                        'score': 35372.176673999995, 'count': 164, 'flag': 'BR'}, '50': {'user_id': 62702050,
                        'user_name': 'Alexander L.', 'score': 34526.29163999999, 'count': 136, 'flag': 'TH'},
                        '51': {'user_id': 67242757, 'user_name': 'Leah P.', 'score': 34360.789218000005,
                        'count': 1934, 'flag': 'BR'}, '52': {'user_id': 54092835, 'user_name': 'Charles S.',
                        'score': 34148.163529000005, 'count': 170, 'flag': 'IN'}, '53': {'user_id': 74384166,
                        'user_name': 'Jonas Z. D.', 'score': 34101.926250000004, 'count': 438, 'flag': 'BR'},
                        '54': {'user_id': 17150078, 'user_name': 'Никита .', 'score': 33458.48164500001,
                        'count': 339, 'flag': 'UA'}, '55': {'user_id': 54139918, 'user_name': 'Ramilson S. L.',
                        'score': 32816.86743600001, 'count': 814, 'flag': 'BR'}, '56': {'user_id': 62840974,
                         'user_name': 'Samuel S.', 'score': 32790.060000000005, 'count': 93, 'flag': 'DO'},
                         '57': {'user_id': 57751525, 'user_name': 'Hugo F. G. R.', 'score': 32469.93887,
                         'count': 90, 'flag': 'CO'}, '58': {'user_id': 11886413, 'user_name': 'Benjamin T.',
                         'score': 32266.259503999998, 'count': 2370, 'flag': 'FR'}, '59': {'user_id': 74956280, '
                         user_name': 'Sebastian L.', 'score': 32078.978167, 'count': 604, 'flag': 'BR'},
                         '60': {'user_id': 10038763, 'user_name': 'Nur S. B. M. T.', 'score': 31749.560001000038,
                          'count': 229, 'flag': 'SG'}, '61': {'user_id': 15346838, 'user_name': 'Raffaello G. C.',
                          'score': 31387.55332799999, 'count': 282, 'flag': 'LU'}, '62': {'user_id': 58487307,
                          'user_name': 'Connor F.', 'score': 30697.899648, 'count': 56, 'flag': 'BR'},
                          '63': {'user_id': 74703422, 'user_name': '용길 .', 'score': 30400.65881100001,
                          'count': 277, 'flag': 'KR'}, '64': {'user_id': 63867622, 'user_name': 'Dominic W.',
                           'score': 30126.892053999996, 'count': 32, 'flag': 'LA'}, '65': {'user_id': 69559258,
                            'user_name': 'diego s. s.', 'score': 29616.703411000002, 'count': 95, 'flag': 'BR'},
                            '66': {'user_id': 51435178, 'user_name': 'Samuel N.', 'score': 29230.680000000004,
                            'count': 114, 'flag': 'NG'}, '67': {'user_id': 56235289, 'user_name': 'Muhammad M. A.',
                             'score': 29220.588009999996, 'count': 60, 'flag': 'ID'}, '68': {'user_id': 76476054,
                             'user_name': 'Thiago C. d. S.', 'score': 29067.45363400001, 'count': 759, 'flag': 'BR'},
                             '69': {'user_id': 71241878, 'user_name': 'SILVIO L. D. S. J.', 'score': 28453.77092499998,
                             'count': 166, 'flag': 'BR'}, '70': {'user_id': 76686383, 'user_name': 'Ju S. H.',
                             'score': 28330.757488999996, 'count': 29, 'flag': 'KR'}, '71': {'user_id': 76610350,
                             'user_name': 'Asher R.', 'score': 27851.778259999995, 'count': 897, 'flag': 'MK'},
                             '72': {'user_id': 57697337, 'user_name': 'Austin W.', 'score': 27836.562275000008,
                              'count': 57, 'flag': 'BR'}, '73': {'user_id': 53711757, 'user_name': 'Jonathan C.',
                              'score': 27646.925839999985, 'count': 94, 'flag': 'BR'}, '74': {'user_id': 75513774,
                              'user_name': 'Leandro N. Z.', 'score': 27504.669713000018, 'count': 233, 'flag': 'BR'},
                               '75': {'user_id': 55098777, 'user_name': 'Juan S. L. H.', 'score': 27353.723391,
                               'count': 42, 'flag': 'CO'}, '76': {'user_id': 26156370, 'user_name': 'Renato P.',
                               'score': 27305.552034000004, 'count': 43, 'flag': 'BR'}, '77': {'user_id': 38003583,
                                'user_name': 'Connor J.', 'score': 26991.600000000002, 'count': 1985, 'flag': 'BR'},
                                 '78': {'user_id': 13893128, 'user_name': 'Winai S.', 'score': 26664.688607000007,
                                 'count': 369, 'flag': 'TH'}, '79': {'user_id': 55099058,
                                 'user_name': 'Samuel C. K. D. O.', 'score': 26199.122514000017,
                                 'count': 310, 'flag': 'BR'}, '80': {'user_id': 13372908,
                                 'user_name': 'ayman j.', 'score': 26159.783749000002,
                                 'count': 129, 'flag': 'EG'}, '81': {'user_id': 40606850,
                                 'user_name': 'John H.', 'score': 26034.73452599999,
                                 'count': 201, 'flag': 'MX'}, '82': {'user_id': 45447190,
                                 'user_name': 'Jose A.', 'score': 25187.145059000002,
                                 'count': 112, 'flag': 'TH'},
                                 '83': {'user_id': 69864746, 'user_name': 'LAZARO L. E. S.',
                                 'score': 25173.719999000004, 'count': 37, 'flag': 'BR'},
                                 '84': {'user_id': 45408388, 'user_name': 'Claudio O. D. S. S.',
                                 'score': 24832.376128999997, 'count': 323, 'flag': 'BR'}, '85': {'user_id': 30547186,
                                  'user_name': 'Motsumi M.', 'score': 24620.290607000006, 'count': 407, 'flag': 'ZA'},
                                  '86': {'user_id': 63352997, 'user_name': 'Alexandre S. F. D. M.',
                                  'score': 24498.138975, 'count': 34, 'flag': 'BR'},
                                  '87': {'user_id': 74817835, 'user_name': 'Elijah P.',
                                  'score': 24059.392368, 'count': 51, 'flag': 'SG'},
                                  '88': {'user_id': 51564329, 'user_name': 'Jason W.',
                                  'score': 24045.545209999997, 'count': 18, 'flag': 'PK'},
                                  '89': {'user_id': 24085141, 'user_name': 'NILSON S. D. S.',
                                   'score': 23890.67496699999, 'count': 159, 'flag': 'BR'},
                                 '90': {'user_id': 58364228, 'user_name': 'Nicolas F.', 'score': 23884.130227999998,
                                 'count': 91, 'flag': 'CR'},
                        '91': {'user_id': 16312131, 'user_name': 'Kenth-Olov S.', 'score': 23844.958760999987,
                         'count': 674, 'flag': 'SE'},
                        '92': {'user_id': 59439734, 'user_name': 'Connor S.', 'score': 23625.363886000003,
                        'count': 133, 'flag': 'BR'},
                        '93': {'user_id': 69930329, 'user_name': 'MAHASHOOK E.', 'score': 23570.006054000016,
                        'count': 163, 'flag': 'IN'},
                        '94': {'user_id': 70938445, 'user_name': 'Carter A.', 'score': 23555.709998999984,
                        'count': 2590, 'flag': 'VE'},
                        '95': {'user_id': 60183775, 'user_name': 'Kevin J.', 'score': 23343.413663999938,
                        'count': 1250, 'flag': 'SM'},
                        '96': {'user_id': 43739819, 'user_name': 'Edidio S. R.', 'score': 23297.612573000006,
                         'count': 171, 'flag': 'BR'},
                        '97': {'user_id': 63063830, 'user_name': 'sara p.', 'score': 23237.488849000005,
                        'count': 36, 'flag': 'BR'},
                        '98': {'user_id': 47044590, 'user_name': 'Wilmar M.', 'score': 23079.158333000007,
                        'count': 853, 'flag': 'BR'},
                        '99': {'user_id': 73369844, 'user_name': 'Oliver M.', 'score': 22862.551500000005,
                        'count': 199, 'flag': 'PK'},
                        '100': {'user_id': 67658506, 'user_name': 'Rizki A.', 'score': 22757.042248000005,
                        'count': 84, 'flag': 'ID'}},
                        'near_traders': {'306056': {'user_id': 76757666, 'user_name': 'Test T.', 'score': 0.0,
                        'count': 0, 'flag': 'BR'}},
                        'top_countries': {'1': {'country_id': 30, 'name_short': 'BR', 'profit': 19284363.719301555},
                        '2': {'country_id': 194, 'name_short': 'TH', 'profit': 1757536.3707300012},
                        '3': {'country_id': 225, 'name_short': 'IN', 'profit': 1602008.2317870068},
                        '4': {'country_id': 46, 'name_short': 'CO', 'profit': 1601114.0782900564},
                         '5': {'country_id': 212, 'name_short': 'VN', 'profit': 913309.4867309995},
                        '6': {'country_id': 128, 'name_short': 'MX', 'profit': 879294.2022480051},
                        '7': {'country_id': 180, 'name_short': 'ZA', 'profit': 820781.2238850023},
                         '8': {'country_id': 94, 'name_short': 'ID', 'profit': 689486.8343849988},
                        '9': {'country_id': 156, 'name_short': 'PE', 'profit': 538571.1998770044},
                    '10': {'country_id': 205, 'name_short': 'AE', 'profit': 528335.7821359993}}, 'score': 0.0}}
           Raises:
              ValueError: Invalid params country or user_country
              TimeoutError: wait response of server late pooling time informed
        """

        total_args = len(args)
        country = kwargs.get('country', args[0] if total_args > 0 else 'Worldwide')
        from_position = kwargs.get('from_position', args[1] if total_args > 1 else 1)
        to_position = kwargs.get('to_position', args[2] if total_args > 2 else 1)
        near_traders_count = kwargs.get('near_traders_count', args[3] if total_args > 3 else 0)
        user_country_id = kwargs.get('user_country', args[4] if total_args > 4 else 0)
        near_traders_country_count = kwargs.get('near_traders_country_count', args[5] if total_args > 5 else 0)
        top_country_count = kwargs.get('top_country_count', args[6] if total_args > 6 else 0)
        top_count = kwargs.get('top_count', args[7] if total_args > 7 else 0)
        top_type = kwargs.get('top_type', args[8] if total_args > 8 else 2)
        pooling_time = kwargs.get('top_type', args[9] if total_args > 9 else 300)

        if pooling_time <= 30 or pooling_time > 600:
            pooling_time = 600
            logging.error('pooling time must be 30 and 600 ms')
        with self.api.lock_leaderbord_deals_client:
            self.api.leaderboard_deals_client = None
        try:
            country_id = self.api.countries.get_country_id(country)
        except ValueError:
            raise ValueError('the country name is invalid.')
        try:
            if type(user_country_id) is not int:
                user_country_id = self.api.countries.get_country_id(user_country_id)
        except ValueError:
            user_country_id = 0

        self.api.Get_Leader_Board(country_id, user_country_id, from_position, to_position, near_traders_country_count,
                                  near_traders_count, top_country_count, top_count, top_type)
        time.sleep(.2)
        start = time.time()
        while 1:
            with self.api.lock_leaderbord_deals_client:
                if self.api.leaderboard_deals_client:
                    if self.api.leaderboard_deals_client['isSuccessful']:
                        return self.api.leaderboard_deals_client['result']
                    else:
                        logging.error('get-leaderboard-deals failed')
                        return {}
            if time.time() - start > pooling_time:
                msg = 'wait response of iq option server late {} seconds.'.format(pooling_time/60)
                raise TimeoutError(msg)
            time.sleep(.2)

    def get_top_ten_countries(self) -> dict:
        """ Function to get top ten countries

           return:
               A dict of data ranking top ten countries: { ranking : { country name :, profit : }}

           For example:

                {'1': {'country_name': 'Brazil', 'profit': 20283306.309515793},
                '2': {'country_name': 'Thailand', 'profit': 1921195.1081850065},
                '3': {'country_name': 'India', 'profit': 1763547.6178790075},
                '4': {'country_name': 'Colombia', 'profit': 1654171.8981970623},
                '5': {'country_name': 'Vietnam', 'profit': 984552.785571},
                '6': {'country_name': 'Mexico', 'profit': 908087.9020600046},
                '7': {'country_name': 'South Africa', 'profit': 876138.8213250051},
                '8': {'country_name': 'Indonesia', 'profit': 755503.205712998},
                '9': {'country_name': 'United Arab Emirates', 'profit': 599085.4182369991},
                '10': {'country_name': 'Peru', 'profit': 555931.6867790035}}
           Raises:
              TimeoutError: wait response of server late 60 seconds
        """
        try:
            response = defaultdict(dict)
            countries = self.get_leader_board()['top_countries']
            for ranking in countries:
                response[ranking] = {"country_name": self.api.countries.get_country_name(countries[ranking]['name_short']),
                                     "profit": countries[ranking]['profit']}
            return response
        except KeyError:
            logging.error('error getting top ten countries ranking')
            return {}
        except (TimeoutError, ValueError) as e:
            logging.error(e)
            return {}

    def get_positional_ranking_traders(self, country='Worldwide', from_position=1, to_position=100) -> dict:
        """ Function to get top ten countries

         return:

           A dict with Columns position, user_id, user_name, score, count, flag

           Raises:
             ValueError: Invalid params from_position or to_position
             TimeoutError: wait response of server late 60 seconds
        """
        def process_data(data):
            data_cols = defaultdict(dict)
            col_name = []
            col_id = []
            col_position = []
            col_score = []
            col_flag = []
            col_count = []
            for item in data:
                for k, v in item.items():
                    col_position.append(k)
                    col_id.append(v['user_id'])
                    col_name.append(v['user_name'])
                    col_flag.append(v['flag'])
                    col_score.append(v['score'])
                    col_count.append(v['count'])
            data_cols['position'] = col_position
            data_cols['user_name'] = col_name
            data_cols['user_id'] = col_id
            data_cols['score'] = col_score
            data_cols['count'] = col_count
            data_cols['flag'] = col_flag
            return data_cols
        try:
            if from_position > to_position:
                raise ValueError('the from_position value cannot be greater than the to_position value.')
            if to_position > 10000:
                data = []
                step = 10000
                loop = math.ceil(to_position / step)
                from_ = from_position
                to_ = step
                for _ in range(loop):
                    data.append(self.get_leader_board(country=country, from_position=from_,
                                                      to_position=to_)['positional'])
                    from_ += step
                    to_ += step
                    if to_ > to_position:
                        to_ = to_position
                    time.sleep(.2)
                return process_data(data)
            else:
                return process_data([self.get_leader_board(country=country, from_position=from_position,
                                                           to_position=to_position)['positional']])
        except KeyError:
            logging.error('error getting positional ranking {} from {} to {}'.format(country,
                                                                                     from_position, to_position))
            return {}
        except (TimeoutError, ValueError) as e:
            logging.error(e)
            return {}

    def get_instruments(self, type_instrument):
        # type="crypto"/"forex"/"cfd"
        time.sleep(self.suspend)
        with self.api.lock_instruments:
            self.api.instruments = None
        start = time.time()
        while 1:
            self.api.get_instruments(type_instrument)
            time.sleep(1)
            with self.api.lock_instruments:
                if self.api.instruments:
                    return self.api.instruments
            if time.time() - start > 10:
                raise TimeoutError

    def _instruments_input_to_active(self, type_active):
        instruments = self.get_instruments(type_active)
        for ins in instruments["instruments"]:
            self.actives[ins["id"]] = ins["active_id"]

    def _instruments_input_all_in_actives(self):
        self._instruments_input_to_active("crypto")
        self._instruments_input_to_active("forex")
        self._instruments_input_to_active("cfd")

    def _get_all_binary_actives(self):
        init_info = self.get_all_init()
        for dirr in (["binary", "turbo"]):
            for i in init_info["result"][dirr]["actives"]:
                self.actives[(init_info["result"][dirr]
                ["actives"][i]["name"]).split(".")[1]] = int(i)

    def get_all_init(self):
        while 1:
            with self.api.lock_option_init_all_result:
                self.api.api_option_init_all_result = None
            self.api.get_api_option_init_all()
            time.sleep(1)
            start = time.time()
            while 1:
                if time.time() - start > 30:
                    raise TimeoutError('**warning** get all option v2 late 30 sec')
                with self.api.lock_option_init_all_result:
                    if self.api.api_option_init_all_result:
                        if self.api.api_option_init_all_result["isSuccessful"]:
                            return self.api.api_option_init_all_result
                time.sleep(.1)

    def get_all_init_v2(self):
        with self.api.lock_option_init_all_result:
            self.api.api_option_init_all_result_v2 = None
        self.api.get_api_option_init_all_v2()
        time.sleep(.2)
        start_t = time.time()
        while 1:
            with self.api.lock_option_init_all_result:
                if self.api.api_option_init_all_result_v2:
                    return self.api.api_option_init_all_result_v2
            if time.time() - start_t >= 30:
                raise TimeoutError('**warning** get all option v2 late 30 sec')
            time.sleep(.1)

    def get_all_open_time(self, types=('digital', 'binary', 'turbo', 'cfd', 'forex', 'crypto')) -> defaultdict:

        actives = nested_dict(3, dict)

        if 'binary' in types or 'turbo' in types:
            binary_data = self.get_all_init_v2()
            binary_list = ["binary", "turbo"]
            for option in binary_list:
                for actives_id in binary_data[option]["actives"]:
                    active = binary_data[option]["actives"][actives_id]
                    name = str(active["name"]).split(".")[1]
                    if active["enabled"] == True:
                        if active["is_suspended"] == True:
                            actives[option][name]["open"] = False
                        else:
                            actives[option][name]["open"] = True
                    else:
                        actives[option][name]["open"] = active["enabled"]

        if 'digital' in types:
            digital_data = self.get_digital_underlying_list_data()["underlying"]
            for digital in digital_data:
                name = digital["underlying"]
                schedule = digital["schedule"]
                actives["digital"][name]["open"] = False
                for schedule_time in schedule:
                    start = schedule_time["open"]
                    end = schedule_time["close"]
                    if start < time.time() < end:
                        actives["digital"][name]["open"] = True

        instrument_list = list()
        if 'cfd' in types:
            instrument_list.append('cfd')
        if 'forex' in types:
            instrument_list.append('forex')
        if 'crypto' in types:
            instrument_list.append('crypto')

        if len(instrument_list) > 0:
            for instruments_type in instrument_list:
                ins_data = self.get_instruments(instruments_type)["instruments"]
                for detail in ins_data:
                    name = detail["name"]
                    schedule = detail["schedule"]
                    actives[instruments_type][name]["open"] = False
                    for schedule_time in schedule:
                        start = schedule_time["open"]
                        end = schedule_time["close"]
                        if start < time.time() < end:
                            actives[instruments_type][name]["open"] = True
        return actives

    def get_binary_option_detail(self):
        detail = nested_dict(2, dict)
        init_info = self.get_all_init()
        for actives in init_info["result"]["turbo"]["actives"]:
            name = init_info["result"]["turbo"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            detail[name]["turbo"] = init_info["result"]["turbo"]["actives"][actives]
        for actives in init_info["result"]["binary"]["actives"]:
            name = init_info["result"]["binary"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            detail[name]["binary"] = init_info["result"]["binary"]["actives"][actives]
        return detail

    def get_all_profit(self):
        all_profit = nested_dict(2, dict)
        init_info = self.get_all_init()
        for actives in init_info["result"]["turbo"]["actives"]:
            name = init_info["result"]["turbo"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            all_profit[name]["turbo"] = (
                                                100.0 -
                                                init_info["result"]["turbo"]["actives"][actives]["option"]["profit"][
                                                    "commission"]) / 100.0
        for actives in init_info["result"]["binary"]["actives"]:
            name = init_info["result"]["binary"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            all_profit[name]["binary"] = (
                                                 100.0 -
                                                 init_info["result"]["binary"]["actives"][actives]["option"]["profit"][
                                                     "commission"]) / 100.0
        return all_profit

    def get_profile_ansyc(self):
        while not self.api.profile.msg:
            time.sleep(0.1)
        return self.api.profile.msg

    """def get_profile(self):
        while True:
            try:

                respon = self.iqoptionapi.getprofile().json()
                time.sleep(self.suspend)

                if respon["isSuccessful"] == True:
                    return respon
            except:
                logging.error('**error** get_profile try reconnect')
                self.connect()"""

    def get_currency(self):
        balances_raw = self.__get_balances()
        for balance in balances_raw["msg"]:
            if balance["id"] == self.api.global_value.balance_id:
                return balance["currency"]

    def get_balance_id(self):
        return self.api.global_value.balance_id

    """ def get_balance(self):
        self.iqoptionapi.profile.balance = None
        while True:
            try:
                respon = self.get_profile()
                self.iqoptionapi.profile.balance = respon["result"]["balance"]
                break
            except:
                logging.error('**error** get_balance()')

            time.sleep(self.suspend)
        return self.iqoptionapi.profile.balance"""

    def get_balance(self) -> float:
        try:
            balances_raw = self.__get_balances()
            for balance in balances_raw["msg"]:
                if balance["id"] == self.api.global_value.balance_id:
                    return float(balance["amount"])
        except (TimeoutError, TypeError, KeyError):
            logging.error('erro in getting balance. Timeout error.')
            return 0.0

    def __get_balances(self):
        with self.api.lock_balances_raw:
            self.api.balances_raw = None
        self.api.get_balances()
        start = time.time()
        while 1:
            if time.time()-start > 5:
                raise TimeoutError('Server not response late 5 seconds')
            with self.api.lock_balances_raw:
                if self.api.balances_raw:
                    return self.api.balances_raw
            time.sleep(.1)

    def get_balance_mode(self):
        # self.iqoptionapi.profile.balance_type=None
        profile = self.get_profile_ansyc()
        for balance in profile["balances"]:
            if balance["id"] == self.api.global_value.balance_id:
                if balance["type"] == 1:
                    return "REAL"
                elif balance["type"] == 4:
                    return "PRACTICE"
                elif balance["type"] == 2:
                    return "TOURNAMENT"
                else:
                    logging.error('balance indefined.')
                    self.close_connect()
                    return None

    def reset_practice_balance(self):
        with self.api.lock_training_balance_reset:
            self.api.training_balance_reset_request = None
        self.api.reset_training_balance()
        time.sleep(.2)
        while 1:
            with self.api.lock_training_balance_reset:
                if self.api.training_balance_reset_request is not None:
                    return self.api.training_balance_reset_request
            time.sleep(.1)

    def position_change_all(self, main_name, user_balance_id):
        instrument_type = ["cfd", "forex", "crypto", "digital-option", "turbo-option", "binary-option"]
        for ins in instrument_type:
            self.api.portfolio(Main_Name=main_name, name="portfolio.position-changed", instrument_type=ins,
                               user_balance_id=user_balance_id)

    def order_changed_all(self, main_name):
        instrument_type = ["cfd", "forex", "crypto", "digital-option", "turbo-option", "binary-option"]
        for ins in instrument_type:
            self.api.portfolio(Main_Name=main_name, name="portfolio.order-changed", instrument_type=ins)

    def set_tournament(self, balance_mode):
        def set_id(obj, b_id):
            if obj.global_value.balance_id:
                obj.position_change_all("unsubscribeMessage", obj.global_value.balance_id)
            obj.global_value.balance_id = b_id
            obj.position_change_all("subscribeMessage", b_id)

        real_id = None
        practice_id = None
        tournament_id = None

        for balance in self.get_profile_ansyc()["balances"]:
            if balance["type"] == 1:
                real_id = balance["id"]
            if balance["type"] == 4:
                practice_id = balance["id"]
            if balance["tournament_name"] == balance_mode:
                tournament_id = balance["id"]

        if balance_mode == "REAL":
            set_id(self, real_id)

        elif balance_mode == "PRACTICE":
            set_id(self, practice_id)

        else:
            if tournament_id:
                set_id(self, tournament_id)
            else:
                logging.error("ERROR doesn't have this mode")
                self.close_connect()

    def change_balance(self, balance_mode) -> bool:
        """ Function for change type balance

            Has 2 balance types : PRACTICE or REAL

            args:
              balance_mode: (str) 'PRACTICE or 'REAL'

            returns:
              bool with result. True for successful change or False for not.

            raise:
              ValueError: balance mode not 'PRACTICE or 'REAL'
              ConnectionError: for undefined balance mode
        """
        def set_id(obj, b_id):
            if obj.api.global_value.balance_id:
                obj.position_change_all("unsubscribeMessage", obj.api.global_value.balance_id)
            obj.api.global_value.balance_id = b_id
            obj.position_change_all("subscribeMessage", b_id)
        if balance_mode not in ['PRACTICE', 'REAL']:
            raise ValueError("ERROR doesn't have this mode")
        real_id = None
        practice_id = None
        for balance in self.get_profile_ansyc()["balances"]:
            if balance["type"] == 1:
                real_id = balance["id"]
            if balance["type"] == 4:
                practice_id = balance["id"]
        if balance_mode == "REAL":
            set_id(self, real_id)
        elif balance_mode == "PRACTICE":
            set_id(self, practice_id)
        else:
            logging.error("ERROR doesn't have this mode")
            self.close_connect()
            raise ConnectionError("ERROR doesn't have this mode")
        return True

    # ________________________________________________________________________
    # _______________________        CANDLE      _____________________________
    # ________________________self.iqoptionapi.getcandles() wss________________________

    def get_candles(self, ACTIVES, interval, count, endtime):
        self.api.candles.candles_data = None
        while True:
            try:
                self.api.getcandles(
                    self.actives[ACTIVES], interval, count, endtime)
                while self.check_connect and self.api.candles.candles_data == None:
                    pass
                if self.api.candles.candles_data != None:
                    break
            except:
                logging.error('**error** get_candles need reconnect')
                self.connect()
        return self.api.candles.candles_data

    #######################################################
    # ______________________________________________________
    # _____________________REAL TIME CANDLE_________________
    # ______________________________________________________
    #######################################################

    def start_candles_stream(self, ACTIVE, size, maxdict):

        if size == "all":
            for s in self.size:
                self.full_realtime_get_candle(ACTIVE, s, maxdict)
                with self.api.lock_real_time_candles:
                    self.api.real_time_candles_maxdict_table[ACTIVE][s] = maxdict
            self.start_candles_all_size_stream(ACTIVE)
        elif size in self.size:
            with self.api.lock_real_time_candles:
                self.api.real_time_candles_maxdict_table[ACTIVE][size] = maxdict
            self.full_realtime_get_candle(ACTIVE, size, maxdict)
            self.start_candles_one_stream(ACTIVE, size)
        else:
            logging.error('**error** start_candles_stream please input right size')

    def stop_candles_stream(self, ACTIVE, size):
        if size == "all":
            self.stop_candles_all_size_stream(ACTIVE)
        elif size in self.size:
            self.stop_candles_one_stream(ACTIVE, size)
        else:
            logging.error(
                '**error** start_candles_stream please input right size')

    def get_realtime_candles(self, ACTIVE, size):
        if size == "all":
            try:
                with self.api.lock_real_time_candles:
                    return self.api.real_time_candles[ACTIVE]
            except:
                logging.error('**error** get_realtime_candles() size="all" can not get candle')
                return False
        elif size in self.size:
            try:
                with self.api.lock_real_time_candles:
                    return self.api.real_time_candles[ACTIVE][size]
            except:
                logging.error('**error** get_realtime_candles() size=' + str(size) + ' can not get candle')
                return False
        else:
            logging.error('**error** get realtime candles please input right "size"')

    def get_all_realtime_candles(self):
        with self.api.lock_real_time_candles:
            return self.api.real_time_candles

    ################################################
    # ---------REAL TIME CANDLE Subset Function---------
    ################################################
    # ---------------------full dict get_candle-----------------------
    def full_realtime_get_candle(self, ACTIVE, size, maxdict):
        candles = self.get_candles(ACTIVE, size, maxdict, self.api.timesync.server_timestamp)
        for can in candles:
            with self.api.lock_real_time_candles:
                self.api.real_time_candles[str(ACTIVE)][int(size)][can["from"]] = can

    # ------------------------Subscribe ONE SIZE-----------------------
    def start_candles_one_stream(self, ACTIVE, size):
        if (str(ACTIVE + "," + str(size)) in self.subscribe_candle) == False:
            self.subscribe_candle.append((ACTIVE + "," + str(size)))
        start = time.time()
        with self.api.lock_real_time_candles:
            self.api.candle_generated_check[str(ACTIVE)][int(size)] = {}
        while 1:
            if time.time() - start > 20:
                logging.error('**error** start_candles_one_stream late for 20 sec')
                return False
            try:
                with self.api.lock_real_time_candles:
                    if self.api.candle_generated_check[str(ACTIVE)][int(size)] == True:
                        return True
            except:
                pass
            try:
                self.api.subscribe(self.actives[ACTIVE], size)
            except:
                logging.error('**error** start_candles_stream reconnect')
                self.connect()
            time.sleep(1)

    def stop_candles_one_stream(self, ACTIVE, size):
        if ((ACTIVE + "," + str(size)) in self.subscribe_candle) == True:
            self.subscribe_candle.remove(ACTIVE + "," + str(size))
        while True:
            try:
                with self.api.lock_real_time_candles:
                    if self.api.candle_generated_check[str(ACTIVE)][int(size)] == {}:
                        return True
            except:
                pass
            with self.api.lock_real_time_candles:
                self.api.candle_generated_check[str(ACTIVE)][int(size)] = {}
            self.api.unsubscribe(self.actives[ACTIVE], size)
            time.sleep(self.suspend * 10)

    # ------------------------Subscribe ALL SIZE-----------------------

    def start_candles_all_size_stream(self, ACTIVE):
        with self.api.lock_real_time_candles:
            self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
        if (str(ACTIVE) in self.subscribe_candle_all_size) == False:
            self.subscribe_candle_all_size.append(str(ACTIVE))
        start = time.time()
        while 1:
            if time.time() - start > 20:
                logging.error('**error** fail ' + ACTIVE + ' start_candles_all_size_stream late for 10 sec')
                return False
            try:
                with self.api.lock_real_time_candles:
                    if self.api.candle_generated_all_size_check[str(ACTIVE)] == True:
                        return True
            except:
                pass
            try:
                self.api.subscribe_all_size(self.actives[ACTIVE])
            except:
                logging.error('**error** start_candles_all_size_stream reconnect')
                self.connect()
            time.sleep(1)

    def stop_candles_all_size_stream(self, ACTIVE):
        if (str(ACTIVE) in self.subscribe_candle_all_size) == True:
            self.subscribe_candle_all_size.remove(str(ACTIVE))
        while True:
            try:
                if self.api.candle_generated_all_size_check[str(ACTIVE)] == {}:
                    break
            except:
                pass
            self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
            self.api.unsubscribe_all_size(self.actives[ACTIVE])
            time.sleep(self.suspend * 10)

    # ------------------------top_assets_updated---------------------------------------------

    def subscribe_top_assets_updated(self, instrument_type):
        self.api.Subscribe_Top_Assets_Updated(instrument_type)

    def unsubscribe_top_assets_updated(self, instrument_type):
        self.api.Unsubscribe_Top_Assets_Updated(instrument_type)

    def get_top_assets_updated(self, instrument_type):
        with self.api.lock_top_assets_updated:
            if instrument_type in self.api.top_assets_updated_data:
                return self.api.top_assets_updated_data[instrument_type]
            else:
                return None

    # ------------------------commission_________
    def subscribe_commission_changed(self, types_actives=('binary', 'turbo', 'digital', 'crypto', 'forex', 'cfd')):
        instrument_types = []
        # "binary-option"/"turbo-option"/"digital-option"/"crypto"/"forex"/"cfd"
        for type_ in types_actives:
            if type_ in ['binary', 'turbo', 'digital']:
                instrument_types.append('{}-option'.format(type_))
            else:
                instrument_types.append(type_)
        for instrument_type in instrument_types:
            self.api.Subscribe_Commission_Changed(instrument_type)
            time.sleep(.2)

    def unsubscribe_commission_changed(self, types_actives=('binary', 'turbo', 'digital', 'crypto', 'forex', 'cfd')):
        instrument_types = []
        # "binary-option"/"turbo-option"/"digital-option"/"crypto"/"forex"/"cfd"
        for type_ in types_actives:
            if type_ in ['binary', 'turbo', 'digital']:
                instrument_types.append('{}-option'.format(type_))
            else:
                instrument_types.append(type_)
        for instrument_type in instrument_types:
            self.api.Unsubscribe_Commission_Changed(instrument_type)
            time.sleep(.2)

    def get_commission_change(self, instrument_type):
        if instrument_type in ['binary', 'turbo', 'digital']:
            instrument_type = '{}-option'.format(instrument_type)
        with self.api.lock_subscribe_commission:
            return self.api.subscribe_commission_changed_data[instrument_type]

    # -----------------------------------------------

    # -----------------traders_mood----------------------

    def start_mood_stream(self, ACTIVES):
        if ACTIVES not in self.subscribe_mood:
            self.subscribe_mood.append(ACTIVES)

        start = time.time()
        actives = self.actives[ACTIVES]
        while 1:
            if time.time() - start > 60:
                raise TimeoutError('tempo de resposta excedido')
            self.api.subscribe_Traders_mood(actives)
            time.sleep(3)
            try:
                with self.api.lock_mood:
                    self.api.traders_mood[actives]
                break
            except:
                time.sleep(5)

    def stop_mood_stream(self, ACTIVES):
        if ACTIVES in self.subscribe_mood == True:
            del self.subscribe_mood[ACTIVES]
        self.api.unsubscribe_Traders_mood(self.actives[ACTIVES])

    def get_traders_mood(self, ACTIVES):
        # return highter %
        with self.api.lock_mood:
            return self.api.traders_mood[self.actives[ACTIVES]]

    def get_all_traders_mood(self):
        # return highter %
        with self.api.lock_mood:
            return self.api.traders_mood

    ##############################################################################################

    def check_win(self, id_number):
        # 'win':win money 'equal':no win no loose   'loose':loose money
        while 1:
            try:
                listinfodata_dict = self.api.listinfodata.get(id_number)
                if listinfodata_dict["game_state"] == 1:
                    break
            except:
                pass
        self.api.listinfodata.delete(id_number)
        return listinfodata_dict["win"]

    def check_win_v2(self, id_number, polling_time=5):
        while 1:
            check, data = self.get_betinfo(id_number)
            try:
                win = data["result"]["data"][str(id_number)]["win"]
            except:
                pass
            if check and win != "":
                try:
                    return data["result"]["data"][str(id_number)]["profit"] - data["result"]["data"][str(id_number)][
                        "deposit"]
                except:
                    pass
            time.sleep(polling_time)

    def check_win_v3(self, id_number, expiration=1) -> float:
        """
        Function for wait result of order buy options

        This function only will return when the server response result of operation or the time of expiration
        over without response.

        args:
            id_number: (int) ID of Transaction for wait result.
            expiration: (int) value of expiration in minutes of option purchased for time of wait.

        returns:
            a float with monetary result

        raises:
            TimeoutError: If server late more that expiration informed.
        """
        start = time.time()
        expiration *= 60
        # For security, 30 seconds to response after expiration time.
        expiration += 30
        while 1:
            if time.time()-start > expiration:
                raise TimeoutError('The operation result response took longer than the expiration time reported.')
            if self.get_async_order(id_number)["option-closed"] != {}:
                break
            time.sleep(.2)

        return self.get_async_order(id_number)["option-closed"]["msg"]["profit_amount"] - \
               self.get_async_order(id_number)["option-closed"]["msg"]["amount"]

    def check_win_v4(self, id_number) -> tuple:
        try:
            if self.get_async_order(id_number)["option-closed"] == {}:
                return False, None
        except KeyError:
            return False, None
        else:
            return True, self.get_async_order(id_number)["option-closed"]["msg"]["profit_amount"] - \
                   self.get_async_order(id_number)["option-closed"]["msg"]["amount"]

    async def check_win_async(self, id_number):
        try:
            if self.get_async_order(id_number)["option-closed"] == {}:
                return False, None
        except:
            return False, None
        else:
            return True, self.get_async_order(id_number)["option-closed"]["msg"]["profit_amount"] - \
                   self.get_async_order(id_number)["option-closed"]["msg"]["amount"]

    # -------------------get infomation only for binary option------------------------

    def get_betinfo(self, id_number):

        while 1:
            self.api.game_betinfo.isSuccessful = None
            try:
                self.api.get_betinfo(id_number)
            except:
                logging.error( '**error** def get_betinfo  self.iqoptionapi.get_betinfo reconnect')
                self.connect()
            start = time.time()
            while self.api.game_betinfo.isSuccessful == None:
                if time.time() - start > 10:
                    time.sleep(5)
                    break
                time.sleep(1)

            if self.api.game_betinfo.isSuccessful:
                return self.api.game_betinfo.isSuccessful, self.api.game_betinfo.dict
            else:
                return self.api.game_betinfo.isSuccessful, None

    def get_optioninfo(self, limit) -> tuple:
        with self.api.lock_api_game_getoptions:
            self.api.api_game_getoptions_result = None
        self.api.get_options(limit)
        time.sleep(1)
        start = time.time()
        while 1:
            if time.time()-start > 30:
                raise TimeoutError('without response server in 30 seconds of request.')
            with self.api.lock_api_game_getoptions:
                if self.api.api_game_getoptions_result:
                    try:
                        if self.api.api_game_getoptions_result['msg']['isSuccessful']:
                            return True, self.api.api_game_getoptions_result['msg']['result']
                        else:
                            return False, self.api.api_game_getoptions_result['msg']['message']
                    except KeyError:
                        return False, 'Error in getting data of options'
            time.sleep(.2)

    def get_optioninfo_v2(self, limit):
        with self.api.lock_get_options_v2:
            self.api.get_options_v2_data = None
        self.api.get_options_v2(limit, "binary,turbo")
        time.sleep(1)
        while 1:
            with self.api.lock_get_options_v2:
                if self.api.get_options_v2_data:
                    return self.api.get_options_v2_data

    # __________________________BUY__________________________

    # __________________FOR OPTION____________________________

    def buy_multi(self, prices_list, actives_list, directions_list, expirations_list) -> list:
        """
               Function for buy list binary or turbo option by raw expirations

               Important: This function only works with binary or turbo options.
               The len of the lists must be equals. The values of price, active, direction and expiration must
               be equal index in list for correct execution.

               args:
                  prices_list: (list) List of prices for buy.
                  actives_list: (list) List of Ticker for Active for buy.
                  directions_list: (list) List of direction for order (call or put).
                  expirations_list: (list) List of expirations of order.

               returns:
                   returns a list with ids of positions. Case any order not executed,
                   the returns item of list will be None. The index of list will be equal of order of
                   received list of orders.
               """
        with self.api.lock_buy_multi:
            self.api.buy_multi_option = {}
        buy_len = len(prices_list)
        if buy_len == len(actives_list) == len(directions_list) == len(expirations_list):
            for idx in range(buy_len):
                try:
                    self.api.buyv3(prices_list[idx], self.actives[actives_list[idx]], directions_list[idx],
                                   expirations_list[idx], idx)
                except KeyError:
                    msg = 'there was a problem getting the active code with ticker {}.'.format(actives_list[idx])
                    raise ValueError(msg)
            while 1:
                with self.api.lock_buy_multi:
                    if len(self.api.buy_multi_option) >= buy_len:
                        buy_id = list()
                        for key in sorted(self.api.buy_multi_option.keys()):
                            try:
                                value = self.api.buy_multi_option[str(key)]
                                buy_id.append(value["id"])
                            except KeyError:
                                buy_id.append(None)
                        return buy_id
                time.sleep(.2)
        else:
            raise ValueError('The  len of lists of datas not equals')

    def get_remaning(self, duration) -> int:
        for remaning in get_remaning_time(self.api.timesync.server_timestamp):
            if remaning[0] == duration:
                return remaning[1]
        return 0

    def buy_by_raw_expirations(self, price, active, direction, type_option, expired) -> tuple:
        """
        Function for buy binary or turbo option by raw expirations

        Important: This function only works with binary or turbo options

        args:
           price: (int) value of order for buy. Mínimum: 1.
           active: (str) Ticker for Active for buy. For example: "EURUSD"
           direction: (str) call or put.
           type_option: (str) turbo or binary.
           expired: (int) times of expiration for buy

        returns:
            returns a tuple result (True / False) and id (Case result True, with ID of transaction,
            else False, reason of failure)
        """
        with self.api.lock_buy_multi:
            self.api.buy_multi_option = {}
        with self.api.lock_buy:
            self.api.buy_successful = None
        req_id = "buyraw"
        try:
            with self.api.lock_buy_multi:
                self.api.buy_multi_option[req_id]["id"] = None
        except KeyError:
            pass
        try:
            self.api.buyv3_by_raw_expired(price, self.actives[active], direction, type_option, expired,
                                          request_id=req_id)
        except KeyError:
            return False, 'there was a problem getting the active code with ticker {}.'.format(active)
        start_t = time.time()
        id_order = None
        with self.api.lock_buy_multi:
            self.api.result = None
        while 1:
            if time.time() - start_t >= 5:
                logging.error('**warning** buy late 5 sec')
                return False, 'Timeout response ID Buy'
            with self.api.lock_buy_multi:
                try:
                    id_order = self.api.buy_multi_option[req_id]["id"]
                except KeyError:
                    pass
                if self.api.result or id_order:
                    if "message" in self.api.buy_multi_option[req_id].keys():
                        logging.error('**warning** buy' + str(self.api.buy_multi_option[req_id]["message"]))
                        return False, self.api.buy_multi_option[req_id]["message"]
                    return self.api.result, id_order
            time.sleep(.2)

    def buy(self, price, active, direction, expirations=1) -> tuple:
        """
        Function for buy binary or turbo option

        Important: This function only works with binary or turbo options

        args:
           price: (int) value of order for buy. Mínimum: 1.
           active: (str) Ticker for Active for buy. For example: "EURUSD"
           direction: (str) call or put.
           expiration: (int) times of expiration for buy

        returns:
            returns a tuple result (True / False) and id (Case result True, with ID of transaction,
            else False, reason of failure)
        """
        with self.api.lock_buy:
            self.api.buy_successful = None
        try:
            with self.api.lock_buy_multi:
                self.api.buy_multi_option = {}
                self.api.buy_multi_option["buy"]["id"] = None
        except KeyError:
            pass
        try:
            self.api.buyv3(price, self.actives[active], direction, expirations, "buy")
        except KeyError:
            return False, 'there was a problem getting the active code with ticker {}.'.format(active)
        start_t = time.time()
        id_buy = None
        with self.api.lock_buy_multi:
            self.api.result = None
        while 1:
            if time.time() - start_t >= 10:
                logging.error('**warning** buy late 10 sec')
                return False, 'Timeout response ID Buy. Verify in IQ Option App or Site if the order was executed.'
            with self.api.lock_buy_multi:
                try:
                    id_buy = self.api.buy_multi_option["buy"]["id"]
                    if self.api.result or id_buy:
                        if "message" in self.api.buy_multi_option["buy"].keys():
                            return False, self.api.buy_multi_option["buy"]["message"]
                        return self.api.result, id_buy
                except (KeyError, ValueError):
                    pass
                except Exception as e:
                    logging.error('get-message-result-buy -> {}'.format(e))
            time.sleep(.1)

    def sell_option(self, options_ids) -> bool:
        with self.api.lock_sold_options_respond:
            self.api.sold_options_respond = None
        self.api.sell_option(options_ids)
        time.sleep(.2)
        start = time.time()
        while 1:
            with self.api.lock_sold_options_respond:
                if self.api.sold_options_respond:
                    return self.api.sold_options_respond
            if time.time()-start > 10:
                logging.error('sell option timeout')
                return False
            time.sleep(.2)

    def get_digital_underlying_list_data(self):
        with self.api.lock_underlying_list:
            self.api.underlying_list_data = None
        self.api.get_digital_underlying()
        time.sleep(.2)
        start_t = time.time()
        while 1:
            if time.time() - start_t > 10:
                raise TimeoutError('**warning** get all option v2 late 10 sec')
            with self.api.lock_underlying_list:
                if self.api.underlying_list_data:
                    return self.api.underlying_list_data
            time.sleep(.2)

    def get_strike_list(self, active, duration) -> tuple:
        """ Function to get strike list of turbo, binary and digital options

            Args:
               active: (string) name of active.
               duration: (int) value of expiration instrument in 1, 5 or 15 minutes
            return:
               A dict with {price : {call : id, put: id}}

               For example:

                   {
                        '0.652290':
                                    {
                                        'call': 'doNZDUSD-OTC202008150223PT1MC065229',
                                        'put':  'doNZDUSD-OTC202008150223PT1MP065229'
                                    },
                        '0.652310':
                                    {
                                        'call': 'doNZDUSD-OTC202008150223PT1MC065231',
                                        'put':  'doNZDUSD-OTC202008150223PT1MP065231'},
                        '0.652330':
                                    {
                                        'call': 'doNZDUSD-OTC202008150223PT1MC065233',
                                        'put':  'doNZDUSD-OTC202008150223PT1MP065233'
                                    },
                        '0.652350':
                                    {
                                        'call': 'doNZDUSD-OTC202008150223PT1MC065235',
                                        'put':  'doNZDUSD-OTC202008150223PT1MP065235'
                                    },
                        '0.652370':
                                    {
                                        'call': 'doNZDUSD-OTC202008150223PT1MC065237',
                                        'put':  'doNZDUSD-OTC202008150223PT1MP065237'}
                                    }
                   }

            Raises:
              ValueError: parameter expiration invalid
        """
        if duration not in self.durations:
            raise ValueError('Value of duration period must be 1, 5 or 15')
        with self.api.lock_strike_list:
            self.api.strike_list = None
        self.api.get_strike_list(active, duration)
        time.sleep(.2)
        ans = {}
        start = time.time()
        while 1:
            if time.time() - start > 5:
                raise TimeoutError('**warning** get strike list late 5 sec')
            with self.api.lock_strike_list:
                if self.api.strike_list:
                    try:
                        for data in self.api.strike_list["msg"]["strike"]:
                            temp = dict()
                            temp["call"] = data["call"]["id"]
                            temp["put"] = data["put"]["id"]
                            ans[("%.6f" % (float(data["value"]) * 10e-7))] = temp
                    except:
                        logging.error('**error** get_strike_list read problem...')
                        return self.api.strike_list, None
                    else:
                        return self.api.strike_list, ans

    def subscribe_strike_list(self, active, expiration_period):
        """ Function to subscribe strike list of digital option

            Args:
               active: (string) name of active.
               expiration_period: (int) value of expiration instrument in 1, 5 or 15 minutes
            Raises:
               ValueError: parameter expiration invalid
        """
        if expiration_period not in self.durations:
            raise ValueError('Value of duration period must be 1, 5 or 15')
        with self.api.lock_instrument_quote:
            self.api.subscribe_instrument_quites_generated(active, expiration_period)

    def unsubscribe_strike_list(self, active, expiration_period):
        """ Function to subscribe strike list of digital option

                    Args:
                       active: (string) name of active.
                       expiration_period: (int) value of expiration instrument in 1, 5 or 15 minutes
                    Raises:
                       ValueError: parameter expiration invalid
        """
        if expiration_period not in self.durations:
            raise ValueError('Value of duration period must be 1, 5 or 15')
        self.api.unsubscribe_instrument_quites_generated(active, expiration_period)
        with self.api.lock_instrument_quote:
            del self.api.instrument_quites_generated_data[active]

    def get_instrument_quites_generated_data(self, active, duration) -> dict:
        """ Function to get data for quites of digital options

            Args:
               active: (string) name of active.
               duration: (int) value of expiration instrument in 1, 5 or 15 minutes
           return:
               A dict with quites generated data


               For example:

               {'active': 76,
                'expiration': {
                                'instant': '2020-08-15T02:38:00Z',
                                'period': 60,
                                'timestamp': 1597459080000},
                                'instant': '2020-08-15T02:37:03Z',
                                'kind': 'digital-option',
                                'quotes': [{'price': { 'ask': 42.065502, 'bid': 1.0 },
                                            'symbols': ['doEURUSD-OTC202008150238PT1MP11839']},
                                           {'price': { 'ask': 46.133311, 'bid': 1.0 },
                                            'symbols': ['doEURUSD-OTC202008150238PT1MP11841']},
                                           {'price': {'ask': 53.449076, 'bid': 48.649076},
                                            'symbols': ['doEURUSD-OTC202008150238PT1MCSPT']},
                                           {'price': {'ask': 42.091824, 'bid': 1.0},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MC118438']},
                                           {'price': {'ask': 38.261337, 'bid': 24.31197},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MP118416']},
                                           {'price': {'ask': 44.894468, 'bid': 38.484254},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MC118421']},
                                           {'price': {'ask': 37.01829, 'bid': 23.020743},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MC118423']},
                                           {'price': {'ask': None, 'bid': 79.058811},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MC118412']},
                                           {'price': {'ask': 60.172535, 'bid': 51.782535},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MC118419']},
                                           {'price': {'ask': 50.373892, 'bid': 45.622162},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MP118419']},
                                           {'price': {'ask': 50.074479, 'bid': 1.0},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MC118427']},
                                           {'price': {'ask': None, 'bid': 71.747036},
                                           'symbols': ['doEURUSD-OTC202008150238PT1MC118414']},
                                           {'price': {'ask': None, 'bid': 80.0},
                                            'symbols': ['doEURUSD-OTC202008150238PT1MP11845',
                                                        'doEURUSD-OTC202008150238PT1MP118444',
                                                        'doEURUSD-OTC202008150238PT1MC11841',
                                                        'doEURUSD-OTC202008150238PT1MC118408',
                                                        'doEURUSD-OTC202008150238PT1MP118428',
                                                        'doEURUSD-OTC202008150238PT1MP118454',
                                                        'doEURUSD-OTC202008150238PT1MP118436',
                                                        'doEURUSD-OTC202008150238PT1MC118392',
                                                        'doEURUSD-OTC202008150238PT1MP118452']}],
                                            ,
                                'timestamp': 1597459023000,
                                'underlying': 'EURUSD-OTC'}

                    Raises:
                       ValueError: parameter expiration invalid
                """
        start = time.time()
        while 1:
            with self.api.lock_instrument_quote:
                if self.api.instrument_quotes_generated_raw_data[active][duration * 60] != {}:
                    return self.api.instrument_quotes_generated_raw_data[active][duration * 60]['msg']
            if time.time() - start > 60:
                raise TimeoutError('Server response timeout of 60 seconds has been exceeded')
            time.sleep(.1)

    def get_realtime_strike_list(self, active, duration) -> dict:
        """ Function to get strike list of digital options

            Before call this function, need subscribe strike list with function 'subscribe_strike_list'.
            Finish the use of this function, must be unsubscribe with function 'unsubscribe_strike_list'.

            Args:
               active: (string) name of active.
               duration: (int) value of expiration instrument in 1, 5 or 15 minutes
            return:
                A dict with {price : {call : {profit, id}, put : {profit, id}}}
                strikes call / put, profit and id of instrument

                For example:

                {'1.184060':
                            {'call':
                                    {'profit': None,
                                    'id': 'doEURUSD-OTC202008150153PT1MC118406'},
                             'put':
                                    {'profit': 137.72450107570336,
                                    'id': 'doEURUSD-OTC202008150153PT1MP118406'}},
                 '1.184090':
                            {'call':
                                    {'profit': None,
                                      'id': 'doEURUSD-OTC202008150153PT1MC118409'},
                             'put':
                                    {'profit': 137.72450107570336,
                                     'id': 'doEURUSD-OTC202008150153PT1MP118409'}},
                '1.184120':
                            {'call':
                                    {'profit': None,
                                     'id': 'doEURUSD-OTC202008150153PT1MC118412'},
                             'put':
                                    {'profit': 137.72450107570336,
                                    'id': 'doEURUSD-OTC202008150153PT1MP118412'
                                    }
                            }
                }

            Raises:
               ValueError: parameter expiration invalid
        """
        if duration not in self.durations:
            raise ValueError('Value of duration period must be 1, 5 or 15')
        start_t = time.time()
        while 1:
            if time.time()-start_t > 10:
                msg = 'the instrument ' + active + ' has suspended'
                raise InstrumentSuspendedError(msg)
            with self.api.lock_instrument_quote:
                if self.api.instrument_quites_generated_data[active][duration * 60]:
                    break
            time.sleep(.1)
        ans = {}
        with self.api.lock_instrument_quote:
            now_timestamp = self.api.instrument_quites_generated_timestamp[active][duration * 60]

        while ans == {}:
            with self._lock_strike_list:
                if self.get_realtime_strike_list_temp_data == {} \
                        or now_timestamp != self.get_realtime_strike_list_temp_expiration:
                    raw_data, strike_list = self.get_strike_list(active, duration)
                    self.get_realtime_strike_list_temp_expiration = raw_data["msg"]["expiration"]
                    self.get_realtime_strike_list_temp_data = strike_list
                else:
                    strike_list = self.get_realtime_strike_list_temp_data
            with self.api.lock_instrument_quote:
                profit = self.api.instrument_quites_generated_data[active][duration * 60]
            for price_key in strike_list:
                try:
                    side_data = {}
                    for side_key in strike_list[price_key]:
                        detail_data = {}
                        profit_d = profit[strike_list[price_key][side_key]]
                        detail_data["profit"] = profit_d
                        detail_data["id"] = strike_list[price_key][side_key]
                        side_data[side_key] = detail_data
                    ans[price_key] = side_data
                except KeyError:
                    pass
        return ans

    def get_actives_by_profit(self, types_active=('digital', 'binary', 'turbo'),
                              duration=1, minimum_profit=50.0) -> defaultdict:
        """ Function get assets opened by minimum profit percent

            Args:
               types_active: Tuple(str, str, str) Types desired in ('digital', 'binary', 'turbo').
               duration: (int) value of expiration instrument in 1, 5 or 15 minutes
               minimum_profit: (float) Percentual between 0 and 100 for profit

            return:
               defaultdict with actives (key) and % profit (value) grouped by type

            For example:
                        {'turbo':
                            {'GBPUSD-OTC': 0.8, 'EURUSD-OTC': 0.8, 'EURGBP-OTC': 0.8, 'NZDUSD-OTC': 0.8,
                            'EURJPY-OTC': 0.8, 'AUDCAD-OTC': 0.8, 'USDCHF-OTC': 0.8}),
                        'binary':
                           {'GBPUSD-OTC': 0.85, 'EURUSD-OTC': 0.85, 'EURGBP-OTC': 0.85, 'NZDUSD-OTC': 0.85,
                           'AUDCAD-OTC': 0.85, 'USDCHF-OTC': 0.85}),
                        'digital':
                           {'EURUSD-OTC': 0.8708580722352896, 'EURGBP-OTC': 0.8708459969339827,
                            'USDCHF-OTC': 0.9511830774203885, 'EURJPY-OTC': 0.7605998941316072,
                            'NZDUSD-OTC': 0.951184067270895, 'GBPUSD-OTC': 0.8708869835900572,
                            'GBPJPY-OTC': 0.7605185614464816, 'USDJPY-OTC': 0.7605968874161145,
                            'AUDCAD-OTC': 0.9512546918894692})}

            Raises:
                 ValueError: invalid parameters
                 TimeoutError: without response of server in limit time
         """
        if duration not in self.durations:
            raise ValueError('duration invalid. Must be 1, 5 or 15.')
        if minimum_profit < 0 or minimum_profit > 100:
            raise ValueError('Minimum profit is must be between 0 and 100')
        response = nested_dict(2, float)
        all_assets = self.get_all_open_time(types=types_active)
        turbo = True if 'turbo' in types_active else False
        binary = True if 'binary' in types_active else False
        digital = True if 'digital' in types_active else False
        minimum_profit /= 100
        if turbo or binary:
            binaries_assets = self.get_all_profit()
            for k, v in binaries_assets.items():
                if turbo:
                    try:
                        if v['turbo'] >= minimum_profit and all_assets['turbo'][k]['open']:
                            response['turbo'][k] = float(v['turbo'])
                    except (KeyError, TypeError):
                        pass
                if binary:
                    try:
                        if v['binary'] >= minimum_profit and all_assets['binary'][k]['open']:
                            response['binary'][k] = float(v['binary'])
                    except (KeyError, TypeError):
                        pass
        if digital:
            for k, v in all_assets['digital'].items():
                if v['open']:
                    subs = True if (k, duration) in self.__subscribed_strike_list else False
                    self.subscribe_strike_list(k, duration)
                    time.sleep(.2)
                    profit = .0
                    start = time.time()
                    while not profit:
                        if time.time()-start > 5:
                            break
                        profit = self.get_digital_current_profit(k, duration)
                        time.sleep(.2)
                    if profit:
                        profit /= 100
                        if profit >= minimum_profit and all_assets['digital'][k]['open']:
                            response['digital'][k] = float(profit)
                    self.unsubscribe_strike_list(k, duration)
        return response

    def get_digital_current_profit(self, active, duration) -> float:
        """ Function to current profit for digital option

            Before call this function, need subscribe strike list with function 'subscribe_strike_list'.
            Finish the use of this function, must be unsubscribe with function 'unsubscribe_strike_list'.

            Args:
              active: (string) name of active.
              duration: (int) value of expiration instrument in 1, 5 or 15 minutes

           return:
               A float value with current profit, or 0.0 for invalid or not subscribe actives

               For example:   87.09650521515

           Raises:
               ValueError: parameter duration is invalid
               InstrumentUnsubscribeError: Indicate that not subscribed in strike list update for duration informed
        """
        response = .0
        if duration not in self.durations:
            raise ValueError('The duration value must be 1, 5 or 15.')
        try:
            with self.api.lock_instrument_quote:
                profit = self.api.instrument_quites_generated_data[active][duration * 60]
            for key in profit:
                if key.find("SPT") != -1:
                    response = profit[key]
                    break
        except KeyError:
            raise InstrumentUnsubscribeError('Asset {} in duration {} is not subscribed to receive a strike list '
                                             'update.'.format(active, duration))
        finally:
            return response

    def buy_digital_spot(self, active, amount, action, duration):
        # Expiration time need to be formatted like this: YYYYMMDDHHII
        # And need to be on GMT time
        # Type - P or C
        if action == 'put':
            action = 'P'
        elif action == 'call':
            action = 'C'
        else:
            logging.error('buy_digital_spot active error')
            return -1
        # doEURUSD201907191250PT5MPSPT
        timestamp = int(self.api.timesync.server_timestamp)
        if duration == 1:
            exp, _ = get_expiration_time(timestamp, duration)
        else:
            now_date = datetime.fromtimestamp(timestamp) + timedelta(minutes=1, seconds=30)
            while 1:
                if now_date.minute % duration == 0 and time.mktime(now_date.timetuple()) - timestamp > 30:
                    break
                now_date = now_date + timedelta(minutes=1)
            exp = time.mktime(now_date.timetuple())
        dateFormated = str(datetime.utcfromtimestamp(exp).strftime("%Y%m%d%H%M"))
        instrument_id = "do" + active + dateFormated + "PT" + str(duration) + "M" + action + "SPT"
        with self.api.lock_digital_option_placed_id:
            self.api.digital_option_placed_id = None
        self.api.place_digital_option(instrument_id, amount)
        time.sleep(.2)
        while 1:
            with self.api.lock_digital_option_placed_id:
                if self.api.digital_option_placed_id is not None:
                    if isinstance(self.api.digital_option_placed_id, int):
                        return True, self.api.digital_option_placed_id
                    else:
                        return False, self.api.digital_option_placed_id
            time.sleep(.2)

    def get_digital_spot_profit_after_sale(self, position_id) -> float:
        """
        Function for get profit after sale for digital option

        Autor: Lu-Yi-Hsun 2019/11/04
        email: Yihsun1992@gmail.com

        reference: https://github.com/Lu-Yi-Hsun/Decompiler-IQ-Option/blob/master/Source%20Code/5.27.0/
                   sources/com/iqoption/dto/entity/position/Position.java#L564

        """
        def get_instrument_id_to_bid(data, instrument_id):
            for row in data["quotes"]:
                if row["symbols"][0] == instrument_id:
                    return row["price"]["bid"]
            return None
        start = time.time()
        while self.get_async_order(position_id)["position-changed"] == {}:
            if time.time()-start > 5:
                raise TimeoutError('Server response timeout of 5 seconds has been exceeded')
            time.sleep(.1)
        position = self.get_async_order(position_id)["position-changed"]["msg"]
        logging.debug('get_digital_spot_profit_after_sale: Position Info -> {}'.format(position))
        # doEURUSD201911040628PT1MPSPT
        # z mean check if call or not
        direction_instrument = position['raw_event']['instrument_dir']
        if position["instrument_id"].find("MPSPT"):
            z = False
        elif position["instrument_id"].find("MCSPT"):
            z = True
        else:
            logging.error('get_digital_spot_profit_after_sale position error' + str(position["instrument_id"]))
            raise PositionError("Error getting direction of digital option position in "
                                "'get_digital_spot_profit_after_sale'")

        duration = int(position['raw_event']['instrument_period']/60)
        active = position['raw_event']['instrument_underlying']
        amount = max(position['raw_event']["buy_amount"], position['raw_event']["sell_amount"])
        abs_count = position['raw_event']["count"]
        strike_value = position['raw_event']["instrument_strike_value"] / 1000000.0
        lower_strike = position['raw_event']["extra_data"]["lower_instrument_strike"] / 1000000.0
        upper_strike = position['raw_event']["extra_data"]["upper_instrument_strike"] / 1000000.0
        aVar = position['raw_event']["extra_data"]["lower_instrument_id"]
        aVar2 = position['raw_event']["extra_data"]["upper_instrument_id"]
        getRate = position['raw_event']["currency_rate"]
        try:
            instrument_quites_generated_data = self.get_instrument_quites_generated_data(active, duration)
        except TimeoutError:
            raise InstrumentUnsubscribeError('to call this function need subscribe strike list for receive update')
        # https://github.com/Lu-Yi-Hsun/Decompiler-IQ-Option/blob/master/Source%20Code/5.5.1/
        # sources/com/iqoption/dto/entity/position/Position.java#L493
        f_tmp = get_instrument_id_to_bid(instrument_quites_generated_data, aVar)
        # f is bidprice of lower_instrument_id ,f2 is bidprice of upper_instrument_id
        if f_tmp:
            self.get_digital_spot_profit_after_sale_data[position_id]["f"] = f_tmp
            f = f_tmp
        else:
            f = self.get_digital_spot_profit_after_sale_data[position_id]["f"]
        f2_tmp = get_instrument_id_to_bid(instrument_quites_generated_data, aVar2)
        if f2_tmp:
            self.get_digital_spot_profit_after_sale_data[position_id]["f2"] = f2_tmp
            f2 = f2_tmp
        else:
            f2 = self.get_digital_spot_profit_after_sale_data[position_id]["f2"]
        if (lower_strike != strike_value) and f and f2:

            if lower_strike > strike_value or strike_value > upper_strike:
                if z:
                    strike_value = (upper_strike - strike_value) / abs(upper_strike - lower_strike)
                    f = abs(f2 - f)
                else:
                    strike_value = (strike_value - upper_strike) / abs(upper_strike - lower_strike)
                    f = abs(f2 - f)
            elif z:
                f += ((strike_value - lower_strike) / (upper_strike - lower_strike)) * (f2 - f)
            else:
                strike_value = (upper_strike - strike_value) / (upper_strike - lower_strike)
                f -= f2
            f = f2 + (strike_value * f)
        if f:
            # price=f/getRate
            # https://github.com/Lu-Yi-Hsun/Decompiler-IQ-Option/blob/master/Source%20Code/5.27.0/sources/com/
            # iqoption/dto/entity/position/Position.java#L603
            price = f / getRate
            # abs_count Reference
            # https://github.com/Lu-Yi-Hsun/Decompiler-IQ-Option/blob/master/Source%20Code/5.27.0/sources/
            # com/iqoption/dto/entity/position/Position.java#L450
            return float(price * abs_count - amount)
        else:
            return 0.0

    def buy_digital(self, amount, instrument_id):
        with self.api.lock_digital_option_placed_id:
            self.api.digital_option_placed_id = None
        self.api.place_digital_option(instrument_id, amount)
        time.sleep(1)
        start = time.time()
        while 1:
            with self.api.lock_digital_option_placed_id:
                if self.api.digital_option_placed_id != None:
                    return True, self.api.digital_option_placed_id
            if time.time() - start > 30:
                logging.error('buy_digital loss digital_option_placed_id')
                return False, None
            time.sleep(.2)

    def close_digital_option(self, position_id):
        with self.api.lock_buy_multi:
            self.api.result = None
        while self.get_async_order(position_id)["position-changed"] == {}:
            time.sleep(.2)
        position_changed = self.get_async_order(position_id)["position-changed"]["msg"]
        self.api.close_digital_option(position_changed["external_id"])
        time.sleep(1)
        while 1:
            with self.api.lock_buy_multi:
                if self.api.result != None:
                    return self.api.result

    def check_win_digital(self, buy_order_id, polling_time=1):
        while 1:
            data = self.get_digital_position(buy_order_id)
            time.sleep(polling_time)
            if data["msg"]["position"]["status"] == "closed":
                if data["msg"]["position"]["close_reason"] == "default":
                    return data["msg"]["position"]["pnl_realized"]
                elif data["msg"]["position"]["close_reason"] == "expired":
                    return data["msg"]["position"]["pnl_realized"] - data["msg"]["position"]["buy_amount"]

    def check_win_digital_v2(self, buy_order_id) -> tuple:
        try:
            while self.get_async_order(buy_order_id)["position-changed"] == {}:
                time.sleep(.2)
            order_data = self.get_async_order(buy_order_id)["position-changed"]["msg"]
            if order_data:
                if order_data["status"] == "closed":
                    if order_data["close_reason"] == "expired":
                        return True, float(order_data["close_profit"] - order_data["invest"])
                    elif order_data["close_reason"] == "default":
                        return True, float(order_data["pnl_realized"])
                else:
                    return False, None
            else:
                return False, None
        except Exception as e:
            logging.error('check_win_digital_v2: error -> {}'.format(e))
            return False, None

    async def check_win_digital_v3(self, buy_order_id):
        try:
            order_data = self.get_async_order(buy_order_id)["position-changed"]["msg"]
            if order_data:
                if order_data["status"] == "closed":
                    if order_data["close_reason"] == "expired":
                        return True, order_data["close_profit"] - order_data["invest"]
                    elif order_data["close_reason"] == "default":
                        return True, order_data["pnl_realized"]
                else:
                    return False, None
            else:
                return False, None
        except:
            return False, None

    # ----------------------------------------------------------
    # -----------------BUY_for__Forex__&&__stock(cfd)__&&__ctrpto

    def buy_order(self, instrument_type, instrument_id, side, amount, leverage,
                  type, limit_price=None, stop_price=None, stop_lose_kind=None, stop_lose_value=None,
                  take_profit_kind=None, take_profit_value=None, use_trail_stop=False,
                  auto_margin_call=False, use_token_for_commission=False):

        with self.api.lock_buy_order_id:
            self.api.buy_order_id = None
        self.api.buy_order(
            instrument_type=instrument_type, instrument_id=instrument_id,
            side=side, amount=amount, leverage=leverage,
            type=type, limit_price=limit_price, stop_price=stop_price,
            stop_lose_value=stop_lose_value, stop_lose_kind=stop_lose_kind,
            take_profit_value=take_profit_value, take_profit_kind=take_profit_kind,
            use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
            use_token_for_commission=use_token_for_commission
        )
        time.sleep(.2)
        order_id = None
        start = time.time()
        while 1:
            if time.time() - start > 30:
                raise TimeoutError('tempo excedido')
            with self.api.lock_buy_order_id:
                if self.api.buy_order_id != None:
                    order_id = self.api.buy_order_id
                    break
            time.sleep(.2)
        check, data = self.get_order(order_id)
        start = time.time()
        while 1:
            if time.time() - start > 30:
                raise TimeoutError('tempo excedido')
            if data.get("status") == "pending_new":
                check, data = self.get_order(self.api.buy_order_id)
            else:
                break
            time.sleep(1)
        if check:
            if data.get("status") != "rejected":
                return True, order_id
            else:
                return False, data.get("reject_status")
        else:
            return False, None

    def change_auto_margin_call(self, ID_Name, ID, auto_margin_call):
        with self.api.lock_auto_margin_call_changed:
            self.api.auto_margin_call_changed_respond = None
        self.api.change_auto_margin_call(ID_Name, ID, auto_margin_call)
        time.sleep(1)
        while 1:
            with self.api.lock_auto_margin_call_changed:
                if self.api.auto_margin_call_changed_respond != None:
                    if self.api.auto_margin_call_changed_respond["status"] == 2000:
                        return True, self.api.auto_margin_call_changed_respond
                    else:
                        return False, self.api.auto_margin_call_changed_respond
            time.sleep(.2)

    def change_order(self, ID_Name, order_id,
                     stop_lose_kind, stop_lose_value,
                     take_profit_kind, take_profit_value,
                     use_trail_stop, auto_margin_call):
        check = True
        if ID_Name == "position_id":
            check, order_data = self.get_order(order_id)
            position_id = order_data["position_id"]
            ID = position_id
        elif ID_Name == "order_id":
            ID = order_id
        else:
            logging.error('change_order input error ID_Name')

        if check:
            with self.api.lock_tpsl_changed_respond:
                self.api.tpsl_changed_respond = None
            self.api.change_order(ID_Name=ID_Name, ID=ID, stop_lose_kind=stop_lose_kind,
                                  stop_lose_value=stop_lose_value, take_profit_kind=take_profit_kind,
                                  take_profit_value=take_profit_value, use_trail_stop=use_trail_stop)
            time.sleep(.5)
            self.change_auto_margin_call(ID_Name=ID_Name, ID=ID, auto_margin_call=auto_margin_call)
            time.sleep(1)
            while 1:
                with self.api.lock_tpsl_changed_respond:
                    if self.api.tpsl_changed_respond != None:
                        if self.api.tpsl_changed_respond["status"] == 2000:
                            return True, self.api.tpsl_changed_respond["msg"]
                        else:
                            return False, self.api.tpsl_changed_respond
                time.sleep(.2)
        else:
            logging.error('change_order fail to get position_id')
            return False, None

    def get_async_order(self, buy_order_id):
        # name': 'position-changed', 'microserviceName': "portfolio"/"digital-options"
        with self.api.lock_position_change:
            return self.api.order_async[buy_order_id]

    def get_order(self, buy_order_id):
        # self.iqoptionapi.order_data["status"]
        # reject:you can not get this order
        # pending_new:this order is working now
        # filled:this order is ok now
        # new
        with self.api.lock_buy_order_id:
            self.api.order_data = None
        self.api.get_order(buy_order_id)
        time.sleep(1)
        start = time.time()
        while 1:
            if time.time() - start > 10:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_buy_order_id:
                if self.api.order_data != None:
                    if self.api.order_data["status"] == 2000:
                        return True, self.api.order_data.get("msg")
                    else:
                        return False, None
            time.sleep(.1)

    def get_pending(self, instrument_type):
        with self.api.lock_deferred_orders:
            self.api.deferred_orders = None
        self.api.get_pending(instrument_type)
        time.sleep(1)
        start = time.time()
        while 1:
            if time.time() - start > 10:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_deferred_orders:
                if self.api.deferred_orders != None:
                    if self.api.deferred_orders["status"] == 2000:
                        return True, self.api.deferred_orders["msg"]
                    else:
                        return False, None
            time.sleep(.2)

    # this function is heavy
    def get_positions(self, instrument_type, time_limit=0):
        with self.api.lock_positions:
            self.api.positions = None
        self.api.get_positions(instrument_type)
        time.sleep(.2)
        start = time.time()
        while 1:
            if time.time() - start > time_limit and time_limit > 0:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_positions:
                if self.api.positions != None:
                    if self.api.positions["status"] == 2000:
                        return True, self.api.positions["msg"]
                    else:
                        return False, None
            time.sleep(.2)

    def get_position(self, buy_order_id):
        with self.api.lock_positions:
            self.api.position = None
        check, order_data = self.get_order(buy_order_id)
        position_id = order_data["position_id"]
        self.api.get_position(position_id)
        time.sleep(.2)
        start = time.time()
        while 1:
            if time.time() - start > 10:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_positions:
                if self.api.position != None:
                    if self.api.position["status"] == 2000:
                        return True, self.api.position["msg"]
                    else:
                        return False, None
            time.sleep(.2)

    # this function is heavy

    def get_digital_position_by_position_id(self, position_id, limit_time=0):
        with self.api.lock_positions:
            self.api.position = None
        self.api.get_digital_position(position_id)
        time.sleep(1)
        start = time.time()
        while 1:
            if time.time() - start > 60 and limit_time > 0:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_positions:
                if self.api.position != None:
                    return self.api.position
            time.sleep(.2)

    def get_digital_position(self, order_id):
        with self.api.lock_positions:
            self.api.position = None
        start = time.time()
        while self.get_async_order(order_id)["position-changed"] == {}:
            if time.time() - start > 5:
                raise TimeoutError('not response of server in 5 seconds')
            time.sleep(.2)
        position_id = self.get_async_order(order_id)["position-changed"]["msg"]["external_id"]
        self.api.get_digital_position(position_id)
        time.sleep(.2)
        start = time.time()
        while 1:
            if time.time() - start > 5:
                raise TimeoutError('not response of server in 5 seconds')
            with self.api.lock_positions:
                if self.api.position:
                    return self.api.position
            time.sleep(.2)

    def get_position_history(self, instrument_type, limit_time=0):
        with self.api.lock_position_history:
            self.api.position_history = None
        self.api.get_position_history(instrument_type)
        time.sleep(1)
        start = time.time()
        while 1:
            if time.time() - start > limit_time and limit_time > 0:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_position_history:
                if self.api.position_history != None:
                    if self.api.position_history["status"] == 2000:
                        return True, self.api.position_history["msg"]
                    else:
                        return False, None
            time.sleep(.2)

    def get_position_history_v2(self, instrument_type, limit, offset, start=0, end=0, limit_time=0):
        # instrument_type=crypto forex fx-option multi-option cfd digital-option turbo-option
        with self.api.lock_position_history:
            self.api.position_history_v2 = None
        self.api.get_position_history_v2(instrument_type, limit, offset, start, end)
        time.sleep(1)
        start = time.time()
        while 1:
            if time.time() - start > limit_time and limit_time > 0:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_position_history:
                if self.api.position_history_v2 != None:
                    if self.api.position_history_v2["status"] == 2000:
                        return True, self.api.position_history_v2["msg"]
                    else:
                        return False, None
            time.sleep(.2)

    def get_position_history_v3(self, user_id, instrument_type, limit, offset, start=0, end=0):
        with self.api.lock_position_history_v3:
            self.api.position_history_v3 = None
        self.api.get_position_history_v3(user_id, instrument_type, limit, offset, start, end)
        time.sleep(1)
        start = time.time()
        while 1:
            if time.time() - start > 60:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_position_history_v3:
                if self.api.position_history_v3:
                    if self.api.position_history_v3["status"] == 2000:
                        return True, self.api.position_history_v3["msg"]
                    else:
                        return False, None
            time.sleep(.2)

    def get_available_leverages(self, instrument_type, actives="", limit_time=0):
        with self.api.lock_leverage:
            self.api.available_leverages = None
        if actives == "":
            self.api.get_available_leverages(instrument_type, "")
        else:
            self.api.get_available_leverages(instrument_type, self.actives[actives])
        time.sleep(.2)
        start = time.time()
        while 1:
            if time.time() - start > limit_time and limit_time > 0:
                raise TimeoutError('tempo de resposta excedido')
            with self.api.lock_leverage:
                if self.api.available_leverages:
                    if self.api.available_leverages["status"] == 2000:
                        return True, self.api.available_leverages["msg"]
                    else:
                        return False, None
                time.sleep(.2)

    def cancel_order(self, buy_order_id):
        with self.api.lock_order_canceled:
            self.api.order_canceled = None
        self.api.cancel_order(buy_order_id)
        time.sleep(1)
        while 1:
            with self.api.lock_order_canceled:
                if self.api.order_canceled:
                    if self.api.order_canceled["status"] == 2000:
                        return True
                    else:
                        return False
            time.sleep(.2)

    def close_position(self, position_id):
        check, data = self.get_order(position_id)
        if data["position_id"]:
            with self.api.lock_close_position_data:
                self.api.close_position_data = None
            self.api.close_position(data["position_id"])
            time.sleep(1)
            while 1:
                with self.api.lock_close_position_data:
                    if self.api.close_position_data:
                        if self.api.close_position_data["status"] == 2000:
                            return True
                        else:
                            return False
                time.sleep(.2)
        else:
            return False

    def close_position_v2(self, position_id):
        while not self.get_async_order(position_id):
            time.sleep(.1)
        position_changed = self.get_async_order(position_id)
        self.api.close_position(position_changed["id"])
        time.sleep(1)
        while 1:
            with self.api.lock_close_position_data:
                if self.api.close_position_data:
                    if self.api.close_position_data["status"] == 2000:
                        return True
                    else:
                        return False
            time.sleep(.2)

    def get_overnight_fee(self, instrument_type, active):
        with self.api.lock_overnight_fee:
            self.api.overnight_fee = None
        self.api.get_overnight_fee(instrument_type, self.actives[active])
        time.sleep(1)
        while 1:
            with self.api.lock_overnight_fee:
                if self.api.overnight_fee:
                    if self.api.overnight_fee["status"] == 2000:
                        return True, self.api.overnight_fee["msg"]
                    else:
                        return False, None
            time.sleep(.2)

    def get_option_open_by_other_pc(self):
        with self.api.lock_socket_option_opened:
            return self.api.socket_option_opened

    def del_option_open_by_other_pc(self, id):
        with self.api.lock_socket_option_opened:
            del self.api.socket_option_opened[id]

    # -----------------------------------------------------------------

    def opcode_to_name(self, opcode):
        return list(self.actives.keys())[list(self.actives.values()).index(opcode)]

    def get_active_id(self, active):
        try:
            return self.actives[active]
        except KeyError:
            logging.error('active {} is invalid'.format(active))
            return None

    def __subscribe_live_deal(self, name, actives, type_actives):
        if type(actives) is list:
            for active in actives:
                active_id = self.get_active_id(active)
                if not active_id:
                    return False, 'active {} is invalid'.format(active)
                self.api.Subscribe_Live_Deal(name, active_id, type_actives)
                time.sleep(.2)
            return True, None
        else:
            active_id = self.get_active_id(actives)
            if not actives:
                return False, 'active {} is invalid'.format(actives)
            self.api.Subscribe_Live_Deal(name, active_id, type_actives)
            return True, None

    def subscribe_live_deal_binary(self, actives, turbo=True) -> tuple:
        """
        Function for subscribe live deals of options binary or turbo.
        param actives:  active or list of actives names
        param turbo: flag for option type turbo
        return Tuple (True/False, reason or message error)
        """

        name = "live-deal-binary-option-placed"
        type_active = "turbo" if turbo else "binary"
        return self.__subscribe_live_deal(name, actives, type_active)

    def subscribe_live_deal_digital(self, actives, expiration=1) -> tuple:
        """
        Function for subscribe live deals of options digital type.
        param actives: (str) or (list) active name or list of actives names
        expiration: (int) expiration time in 1, 5 or 15 minutes
        return Tuple (True/False, reason or message error)
        """
        name = "live-deal-digital-option"
        if expiration not in [1, 5, 15]:
            raise ValueError('the expiration parameter value must be 1, 5 or 15.')
        # "PT1M"/"PT5M"/"PT15M"
        type_active = "PT{}M".format(expiration)
        return self.__subscribe_live_deal(name, actives, type_active)

    @deprecated
    def subscribe_live_deal(self, name, active, _type, buffersize):
        active_id = self.actives[active]
        self.api.Subscribe_Live_Deal(name, active_id, _type)

    def unsubscribe_live_deal_binary(self, actives, turbo=True):
        """
        Function for unsubscribe live deals of options binary or turbo.
        param actives:  active or list of actives names
        param turbo: flag for option type turbo
        return Tuple (True/False, reason or message error)
        """

        name = "live-deal-binary-option-placed"
        type_active = "turbo" if turbo else "binary"
        return self.__unsubscribe_live_deal(name, actives, type_active)

    def unsubscribe_live_deal_digital(self, actives, expiration=1):
        """
        Function for unsubscribe live deals of options digitals.
        param actives:  (str) or (list) name of active or list of actives names
        return (Tuple) (True/False, reason or message error)
        """
        name = "live-deal-binary-option-placed"
        if expiration not in [1, 5, 15]:
            raise ValueError('the expiration parameter value must be 1, 5 or 15.')
        # "PT1M"/"PT5M"/"PT15M"
        type_active = "PT{}M".format(expiration)
        return self.__unsubscribe_live_deal(name, actives, type_active)

    def __unsubscribe_live_deal(self, name, actives, type_actives):
        if type(actives) is list:
            for active in actives:
                active_id = self.get_active_id(active)
                if not active_id:
                    return False, 'active {} is invalid'.format(active)
                self.api.Unscribe_Live_Deal(name, active_id, type_actives)
                time.sleep(.2)
            return True, None
        else:
            active_id = self.get_active_id(actives)
            if not actives:
                return False, 'active {} is invalid'.format(actives)
            self.api.Unscribe_Live_Deal(name, active_id, type_actives)
            return True, None

    @deprecated
    def unscribe_live_deal(self, name, active, _type):
        active_id = self.actives[active]
        self.api.Unscribe_Live_Deal(name, active_id, _type)

    async def get_live_deal_async(self, name, active, _type):
        with self.api.lock_live_deal_data:
            return self.api.live_deal_data[name][active][_type]

    def get_live_deal_digital(self, active, buffer=0) -> deque:
        """Function to return all registered trades for the specified active of digital type for the current session

           Returns a deque containing a dict of live deals returned of IQ Option server

           Args:
               active: (string) name of active
               buffer: (int) number of return deals for call

           Returns:
             A deque of dict with keys: 'amount_enrolled','avatar','country_id','created_at', 'expiration_type','flag',
             'instrument_active_id','instrument_dir', 'instrument_expiration','is_big','name','position_id',
             'user_id','brand_id'.

           For example:

              ({"amount_enrolled":6.0,"avatar":"","country_id":30,"created_at":1597413960301,
                "expiration_type":"PT1M","flag":"BR","instrument_active_id":1,"instrument_dir":"put",
                "instrument_expiration":1597414020000,"is_big":true,"name":"William O.","position_id":12004821753,
                "user_id":76200274,"brand_id":1})

           Raises:
              KeyError: An error occurred accessing the dict of deals. Invalid active or not registered deals for
             current session
        """
        return self.api.live_deal_data_digital.get_live_deals(active, buffer)

    def get_live_deal_binary(self, active, turbo=True, buffer=0) -> deque:
        """Function to return all registered trades for the specified asset for the current session

           Returns a deque containing a dict of live deals returned of IQ Option server

           Args:
               active: (string) name of active
               turbo: (bool) Is turbo or not (binary).
               buffer: (int) number of return deals for call

           Returns:
               A deque of dict with keys: 'active_id', 'amount_enrolled', 'avatar', 'country_id',
              'created_at', 'direction', 'expiration', 'flag', 'is_big', 'name', 'option_id', 'option_type',
              'user_id', 'brand_id'.

           For example:

              ({'active_id': 1, 'amount_enrolled': 6.0, 'avatar': '', 'country_id': 205, 'created_at': 1597403952000,
                'direction': 'call', 'expiration': 1597404000000, 'flag': 'AE', 'is_big': False,
                'name': 'Obaid S. O. H. A.', 'option_id': 7190473575, 'option_type': 'turbo', 'user_id': 7262400,
                'brand_id': 1},
               {'active_id': 1, 'amount_enrolled': 35.0, 'avatar': '', 'country_id': 180,
                'created_at': 1597403952000, 'direction': 'call', 'expiration': 1597404000000, 'flag': 'ZA',
                'is_big': False, 'name': 'Ephraim G.', 'option_id': 7190473547, 'option_type': 'turbo',
                'user_id': 12590610, 'brand_id': 1})

              Raises:
                 KeyError: An error occurred accessing the dict of deals. Invalid active or not registered deals for
                 current session
        """
        if turbo:
            return self.api.live_deal_data_turbo.get_live_deals(active, buffer)
        return self.api.live_deal_data_binary.get_live_deals(active, buffer)

    def get_all_deals_binary(self, active, turbo=True) -> list:
        """Function to return all registered trades for the specified active of types binary or turbo for the
        current session

                Returns a list containing a dict with the registered trade data.

                Args:
                    active: (string) name of active.
                    turbo: (bool) Is turbo or not (binary).

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
        if turbo:
            return self.api.live_deal_data_turbo.get_all_deals(active)
        return self.api.live_deal_data_binary.get_all_deals(active)

    def get_all_deals_digital(self, active, expiration=1) -> list:
        """Function to return all registered trades for the specified active of type digital for the
        current session

                Returns a list containing a dict with the registered trade data.

                Args:
                    active: (string) name of active.
                    expiration: (int) value of expiration instrument in 1, 5 or 15 minutes
                Returns:
                    A list of dict with keys: 'active_id', 'amount_enrolled', 'avatar', 'country_id',
                    'created_at', 'direction', 'expiration', 'flag', 'is_big', 'name', 'option_id', 'option_type',
                    'user_id', 'brand_id'.

                    For example:

                    [{"amount_enrolled":6.0,"avatar":"","country_id":30,"created_at":1597413960301,
                "expiration_type":"PT1M","flag":"BR","instrument_active_id":1,"instrument_dir":"put",
                "instrument_expiration":1597414020000,"is_big":true,"name":"William O.","position_id":12004821753,
                "user_id":76200274,"brand_id":1}]

                Raises:
                    KeyError: An error occurred accessing the dict of deals. Invalid active or not registed deals for
                    current session
                    ValueError: parameter expiration invalid
                """
        if expiration not in [1, 5, 15]:
            raise ValueError('the expiration parameter value must be 1, 5 or 15.')
        try:
            return [deal for deal in self.api.live_deal_data_digital.get_all_deals(active)
                    if deal["expiration_type"] == "PT{}M".format(expiration)]
        except KeyError:
            return []

    @deprecated
    def get_live_deal(self, name, active, _type):
        with self.api.lock_live_deal_data:
            return self.api.live_deal_data[name][active][_type]

    def pop_live_deal(self, name, active, _type):
        with self.api.lock_live_deal_data:
            return self.api.live_deal_data[name][active][_type].pop()

    async def pop_live_deal_async(self, name, active, _type):
        with self.api.lock_live_deal_data:
            return self.api.live_deal_data[name][active][_type].pop()

    async def clear_live_deal_async(self, name, active, _type, buffersize):
        with self.api.lock_live_deal_data:
            self.api.live_deal_data[name][active][_type] = deque(list(), buffersize)

    def clear_live_deal(self, name, active, _type, buffersize):
        with self.api.lock_live_deal_data:
            self.api.live_deal_data[name][active][_type] = deque(list(), buffersize)

    def get_user_profile_client(self, user_id):
        with self.api.lock_user_profile_client:
            self.api.user_profile_client = None
        self.api.Get_User_Profile_Client(user_id)
        time.sleep(.2)
        while 1:
            with self.api.lock_user_profile_client:
                if self.api.user_profile_client:
                    return self.api.user_profile_client
            time.sleep(.1)

    def request_leaderboard_userinfo_deals_client(self, user_id, country):
        with self.api.lock_leaderboard_userinfo:
            self.api.leaderboard_userinfo_deals_client = None
        country_id = None
        if type(country) is not int:
            country_id = self.api.countries.get_country_id(country)
        else:
            country_id = country
        if not country_id:
            raise ValueError('Country id not defined.')
        self.api.Request_Leaderboard_Userinfo_Deals_Client(user_id, country_id)
        time.sleep(.2)
        start = time.time()
        while 1:
            try:
                with self.api.lock_leaderboard_userinfo:
                    if self.api.leaderboard_userinfo_deals_client["isSuccessful"]:
                        return self.api.leaderboard_userinfo_deals_client
            except (KeyError, TypeError):
                pass
            if time.time()-start > 60:
                raise TimeoutError('Unable to get user information. Response time limit exceeded.')
            time.sleep(0.2)

    async def request_leaderboard_userinfo_deals_client_async(self, user_id, country_id):
        with self.api.lock_leaderboard_userinfo:
            self.api.leaderboard_userinfo_deals_client = None
        country_id = self.api.countries.get_country_id(country_id)
        self.api.Request_Leaderboard_Userinfo_Deals_Client(user_id, country_id)
        while 1:
            try:
                with self.api.lock_leaderboard_userinfo:
                    if self.api.leaderboard_userinfo_deals_client["isSuccessful"]:
                        return self.api.leaderboard_userinfo_deals_client
            except KeyError:
                pass
            time.sleep(0.2)

    def get_users_availability(self, user_id) -> dict:
        """Function to get status of user by id

           Returns a dict of status, assets selected

           Args:
             user_id: (int) id of user.

           Returns:
             Dict of status of user.

             For example:

              {'statuses':
                    [{'selected_asset_id': 1,
                      'selected_asset_type': 7,
                      'idle_duration': 8,
                      'selected_instrument_type':
                      'digital-option',
                      'platform_id': 2,
                      'status': 'online',
                      'user_id': 76671954}]}

           Raises:
             TimeoutError: Not response of server in 30 seconds
        """
        with self.api.lock_users_availability:
            self.api.users_availability = None
        self.api.Get_Users_Availability(user_id)
        time.sleep(.2)
        start = time.time()
        while 1:
            with self.api.lock_users_availability:
                if self.api.users_availability:
                    return self.api.users_availability
            if time.time()-start > 30:
                raise TimeoutError('failure in get users data. Timeout Response.')
            time.sleep(.2)
