"""Module for IQ option websocket."""
import json
import logging
import websocket


class WebsocketClient(object):
    """Class for work with IQ option websocket."""

    def __init__(self, api):
        """
        :param api: The instance of :class:`IQOptionAPI
            <iqoptionapi.iqoptionapi.IQOptionAPI>`.
        """
        self.api = api
        self.wss = websocket.WebSocketApp(
            self.api.wss_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open)

    def dict_queue_add(self, dict, maxdict, key1, key2, key3, value):
        if key3 in dict[key1][key2]:
            dict[key1][key2][key3] = value
        else:
            while 1:
                try:
                    dic_size = len(dict[key1][key2])
                except:
                    dic_size = 0
                if dic_size < maxdict:
                    dict[key1][key2][key3] = value
                    break
                else:
                    #del mini key
                    del dict[key1][key2][sorted(dict[key1][key2].keys(), reverse=False)[0]]

    def on_message(self, message):
        """Method to process websocket messages."""
        self.api.global_value.ssl_Mutual_exclusion = True
        logger = logging.getLogger(__name__)
        logger.debug(message)

        message = json.loads(str(message))

        if message["name"] == "timeSync":
            self.api.timesync.server_timestamp = message["msg"]
        #######################################################
        #---------------------for_realtime_candle______________
        #######################################################
        elif message["name"] == "candle-generated":
            actives = self.api.actives
            Active_name = list(actives.keys())[list(actives.values()).index(message["msg"]["active_id"])]
            active = str(Active_name)
            size = int(message["msg"]["size"])
            from_ = int(message["msg"]["from"])
            msg = message["msg"]
            with self.api.lock_real_time_candles:
                maxdict = self.api.real_time_candles_maxdict_table[Active_name][size]
                self.dict_queue_add(self.api.real_time_candles, maxdict, active, size, from_, msg)
                self.api.candle_generated_check[active][size] = True
        elif message["name"] == "options":
            with self.api.lock_get_options_v2:
                self.api.get_options_v2_data=message
        elif message["name"] == "candles-generated":
            actives = self.api.actives
            Active_name = list(actives.keys())[list(actives.values()).index(message["msg"]["active_id"])]
            active = str(Active_name)
            for k, v in message["msg"]["candles"].items():
                v["active_id"] = message["msg"]["active_id"]
                v["at"] = message["msg"]["at"]
                v["ask"] = message["msg"]["ask"]
                v["bid"] = message["msg"]["bid"]
                v["close"] = message["msg"]["value"]
                v["size"] = int(k)
                size = int(v["size"])
                from_ = int(v["from"])
                msg = v
                with self.api.lock_real_time_candles:
                    maxdict = self.api.real_time_candles_maxdict_table[Active_name][size]
                    self.dict_queue_add(self.api.real_time_candles, maxdict, active, size, from_, msg)
            with self.api.lock_real_time_candles:
                self.api.candle_generated_all_size_check[active] = True
        elif message["name"] == "commission-changed":
            actives = self.api.actives
            instrument_type = message["msg"]["instrument_type"]
            active_id = message["msg"]["active_id"]
            Active_name = list(actives.keys())[list(actives.values()).index(active_id)]
            commission = message["msg"]["commission"]["value"]
            with self.api.lock_live_deal_data:
                self.api.subscribe_commission_changed_data[instrument_type][Active_name][self.api.timesync.server_timestamp] = int(commission)
            
        #######################################################
        #______________________________________________________
        #######################################################
        elif message["name"] == "heartbeat":
            try:
                self.api.heartbeat(message["msg"])
            except:
                pass
        elif message["name"] == "balances":
            with self.api.lock_balances_raw:
                self.api.balances_raw = message
        elif message["name"] == "profile":
            #--------------all-------------
            with self.api.lock:
                self.api.profile.msg = message["msg"]
            if self.api.profile.msg != False:
                #---------------------------
                try:
                    with self.api.lock:
                        self.api.profile.balance = message["msg"]["balance"]
                except:
                    pass
                #Set Default account
                if self.api.global_value.balance_id == None:
                    for balance in message["msg"]["balances"]:
                        if balance["type"] == 4:
                            self.api.global_value.balance_id = balance["id"]
                            break
                try:
                    with self.api.lock:
                        self.api.profile.balance_id = message["msg"]["balance_id"]
                except:
                    pass
                try:
                    with self.api.lock:
                        self.api.profile.balance_type = message["msg"]["balance_type"]
                except:
                    pass
                try:
                    self.api.profile.balances = message["msg"]["balances"]
                except:
                    pass
        elif message["name"] == "candles":
            try:
                self.api.candles.candles_data = message["msg"]["candles"]
            except:
                pass
        #Make sure ""self.iqoptionapi.buySuccessful"" more stable
        #check buySuccessful have two fail action
        #if "user not authorized" we get buyV2_result !!!need to reconnect!!!
        #elif "we have user authoget_balancerized" we get buyComplete
        #I Suggest if you get selget_balancef.iqoptionapi.buy_successful==False you need to reconnect iqoption server
        elif message["name"] == "buyComplete":
            try:
                with self.api.lock_buy:
                    self.api.buy_successful = message["msg"]["isSuccessful"]
                    self.api.buy_id= message["msg"]["result"]["id"]
            except:
                pass
        elif message["name"] == "buyV2_result":
            with self.api.lock_buy:
                self.api.buy_successful = message["msg"]["isSuccessful"]
        #*********************buyv3
        #buy_multi_option
        elif message["name"] == "option":
            with self.api.lock_buy_multi:
                self.api.buy_multi_option[str(message["request_id"])] = message["msg"]
        #**********************************************************   
        elif message["name"] == "listInfoData":
            for get_m in message["msg"]:
                self.api.listinfodata.set(get_m["win"], get_m["game_state"], get_m["id"])
        elif message["name"] == "socket-option-opened":
            id=message["msg"]["id"]
            with self.api.lock_socket_option_opened:
                self.api.socket_option_opened[id] = message
        elif message["name"] == "api_option_init_all_result":
            with self.api.lock_option_init_all_result:
                self.api.api_option_init_all_result = message["msg"]
        elif message["name"] == "initialization-data":
            with self.api.lock_option_init_all_result:
                self.api.api_option_init_all_result_v2 = message["msg"]
        elif message["name"] == "underlying-list":
            with self.api.lock:
                self.api.underlying_list_data=message["msg"]
        elif message["name"] == "instruments":
            with self.api.lock_instruments:
                self.api.instruments=message["msg"]
        elif message["name"] == "financial-information":
            with self.api.lock_financial_info:
                self.api.financial_information=message
        elif message["name"] == "position-changed":
            if message["microserviceName"] == "portfolio" and (message["msg"]["source"] == "digital-options") \
                    or message["msg"]["source"] == "trading":
                with self.api.lock_position_change:
                    self.api.order_async[int(message["msg"]["raw_event"]["order_ids"][0])][message["name"]] = message
            elif message["microserviceName"] == "portfolio" and message["msg"]["source"] == "binary-options":
                with self.api.lock_position_change:
                    self.api.order_async[int(message["msg"]["external_id"])][message["name"]] = message
        elif message["name"] == "option-opened":
            with self.api.lock_position_change:
                self.api.order_async[int(message["msg"]["option_id"])][message["name"]] = message
        elif message["name"] == "option-closed":
            with self.api.lock_position_change:
                self.api.order_async[int(message["msg"]["option_id"])][message["name"]] = message
        elif message["name"] == "top-assets-updated":
            with self.api.lock_auto_margin_call_changed:
                self.api.top_assets_updated_data[str(message["msg"]["instrument_type"])] = message["msg"]["data"]
        elif message["name"] == "strike-list":
            with self.api.lock_strike_list:
                self.api.strike_list = message
        elif message["name"] == "api_game_betinfo_result":
            self.api.game_betinfo.process_message(message["msg"])
            #self.api.game_betinfo.isSuccessful = message["msg"]["isSuccessful"]
            #self.api.game_betinfo.dict = message["msg"]
        elif message["name"]=="traders-mood-changed":
            with self.api.lock_mood:
                self.api.traders_mood[message["msg"]["asset_id"]]=message["msg"]["value"]
        #------for forex&cfd&crypto..
        elif message["name"] == "order-placed-temp":
            with self.api.lock:
                self.api.buy_order_id = message["msg"]["id"]
        elif message["name"] == "order":
            with self.api.lock_buy_order_id:
                self.api.order_data = message
        elif message["name"] == "positions":
            with self.api.lock_positions:
                self.api.positions = message
        elif message["name"] == "position":
            with self.api.lock_positions:
                self.api.position = message
        elif message["name"] == "deferred-orders":
            with self.api.lock_deferred_orders:
                self.api.deferred_orders = message
        elif message["name"]=="position-history":
            with self.api.lock_position_history:
                self.api.position_history=message
        elif message["name"]=="history-positions":
            with self.api.lock_position_history:
                self.api.position_history_v2=message
        elif message["name"]=="available-leverages":
            with self.api.lock_leverage:
                self.api.available_leverages=message
        elif message["name"]=="order-canceled":
            with self.api.lock_order_canceled:
                self.api.order_canceled=message
        elif message["name"]=="position-closed":
            with self.api.lock_close_position_data:
                self.api.close_position_data=message
        elif message["name"]=="overnight-fee":
            with self.api.lock_overnight_fee:
                self.api.overnight_fee=message
        elif message["name"]=="api_game_getoptions_result":
            with self.api.lock_api_game_getoptions:
                self.api.api_game_getoptions_result=message
        elif message["name"]=="sold-options":
            with self.api.lock_sold_options_respond:
                self.api.sold_options_respond=message
        elif message["name"]=="tpsl-changed":
            with self.api.lock_tpsl_changed_respond:
                self.api.tpsl_changed_respond=message
        elif message["name"]=="position-changed":
            with self.api.lock_position_change:
                self.api.position_changed=message
        elif message["name"]=="auto-margin-call-changed":
            with self.api.lock_auto_margin_call_changed:
                self.api.auto_margin_call_changed_respond=message
        elif message["name"]=="digital-option-placed":
            try:
                with self.api.lock_digital_option_placed_id:
                    self.api.digital_option_placed_id=message["msg"]["id"]
            except:
                with self.api.lock_digital_option_placed_id:
                    self.api.digital_option_placed_id=message["msg"]
        elif message["name"]=="result":
            with self.api.lock_buy_multi:
                self.api.result=message["msg"]["success"]
        elif message["name"] == "instrument-quotes-generated":
            actives = self.api.actives
            Active_name = list(actives.keys())[list(actives.values()).index(message["msg"]["active"])]
            period = message["msg"]["expiration"]["period"]
            ans = {}
            for data in message["msg"]["quotes"]:
                #FROM IQ OPTION SOURCE CODE
                #https://github.com/Lu-Yi-Hsun/Decompiler-IQ-Option/blob/master/Source%20Code/5.5.1/sources/com/iqoption/dto/entity/strike/Quote.java#L91
                if data["price"]["ask"] == None:
                    ProfitPercent = None
                else:
                    askPrice = (float)(data["price"]["ask"])
                    ProfitPercent = ((100-askPrice)*100)/askPrice
                
                for symble in data["symbols"]:
                    try:
                        """
                        ID SAMPLE:doUSDJPY-OTC201811111204PT1MC11350481
                        dict ID-prodit:{ID:profit}
                        """
                        ans[symble] = ProfitPercent
                    except Exception as exception:
                        logging.error("instrument-quotes-generated: {}".format(exception))
            with self.api.lock_instrument_quote:
                self.api.instrument_quites_generated_timestamp[Active_name][period] = message["msg"]["expiration"]["timestamp"]
                self.api.instrument_quites_generated_data[Active_name][period] = ans
                self.api.instrument_quotes_generated_raw_data[Active_name][period] = message
        elif message["name"] == "training-balance-reset":
            with self.api.lock_training_balance_reset:
                self.api.training_balance_reset_request=message["msg"]["isSuccessful"]
        elif message["name"] == "live-deal-binary-option-placed":
            name=message["name"]
            active_id=message["msg"]["active_id"]
            actives = self.api.actives
            active = list(actives.keys())[list(actives.values()).index(active_id)]
            _type = message["msg"]["option_type"]
            try:
                with self.api.lock_live_deal_data:
                    self.api.live_deal_data[name][active][_type].appendleft(message["msg"])
            except Exception as exception:
                logging.error("live-deal-binary-option-placed: {}".format(exception))
        elif message["name"] == "live-deal-digital-option":
            name = message["name"]
            active_id = message["msg"]["instrument_active_id"]
            actives = self.api.actives
            active = list(actives.keys())[list(actives.values()).index(active_id)]
            _type = message["msg"]["expiration_type"]
            try:
                with self.api.lock_live_deal_data:
                    self.api.live_deal_data[name][active][_type].appendleft(message["msg"])
            except Exception as exception:
                logging.error("live-deal-digital-option:{}".format(exception))
        elif message["name"] == "leaderboard-deals-client":
            with self.api.lock_leaderbord_deals_client:
                self.api.leaderboard_deals_client = message["msg"]
        elif message["name"] == "live-deal":
            name = message["name"]
            active_id = message["msg"]["instrument_active_id"]
            actives = self.api.actives
            active = list(actives.keys())[list(actives.values()).index(active_id)]
            _type = message["msg"]["instrument_type"]
            try:
                with self.api.lock_live_deal_data:
                    self.api.live_deal_data[name][active][_type].appendleft(message["msg"])
            except Exception as exception:
                logging.error("live-deal: {}".format(exception))
        elif message["name"] == "user-profile-client":
            with self.api.lock_user_profile_client:
                self.api.user_profile_client = message["msg"]
        elif message["name"] == "leaderboard-userinfo-deals-client":
            with self.api.lock_leaderboard_userinfo:
                self.api.leaderboard_userinfo_deals_client = message["msg"]
        elif message["name"] == "users-availability":
            with self.api.lock_users_availability:
                self.api.users_availability = message["msg"]
        else:
            pass
        self.api.global_value.ssl_Mutual_exclusion = False

    def on_error(self, error):
        """Method to process websocket errors."""
        logger = logging.getLogger(__name__)
        logger.error(error)
        self.api.global_value.websocket_error_reason = str(error)
        self.api.global_value.check_websocket_if_error = True

    def on_open(self):
        """Method to process websocket open."""
        logger = logging.getLogger(__name__)
        logger.debug("Websocket client connected.")
        self.api.global_value.check_websocket_if_connect = 1

    def on_close(self):
        """Method to process websocket close."""
        logger = logging.getLogger(__name__)
        logger.debug("Websocket connection closed.")
        self.api.global_value.check_websocket_if_connect = 0
