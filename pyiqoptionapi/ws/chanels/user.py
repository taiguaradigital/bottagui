"""Module for IQ option unsubscribe websocket chanel."""
from pyiqoptionapi.ws.chanels.base import Base


class Get_user_profile_client(Base):
   
    name = "sendMessage"

    def __call__(self, user_id):

        data = {"name": "get-user-profile-client",
                "body": {
                            "user_id": int(user_id)
                        },
                "version": "1.0"
               }

        self.send_websocket_request(self.name, data)


class Get_user_profile_client_by_name(Base):

    name = "sendMessage"

    def __call__(self, user_name):
        data = {"name": "get-user-profile-client",
                "body": {
                            "name": user_name
                        },
                "version": "1.0"
                }

        self.send_websocket_request(self.name, data)


class Request_leaderboard_userinfo_deals_client(Base):
    """Class for IQ option candles websocket chanel."""

    name = "sendMessage"

    def __call__(self, user_id,country_id):

        data = {
                "name": "request-leaderboard-userinfo-deals-client",
                "body": {
                          "country_ids": [country_id],
                          "requested_user_id": int(user_id)
                        },
                "version": "1.0"
              }

        self.send_websocket_request(self.name, data)


class Get_users_availability(Base):
    """Class for IQ option candles websocket chanel."""

    name = "sendMessage"

    def __call__(self, user_id):

        data = {
                "name": "get-users-availability",
                "body": {
                         "user_ids": [user_id]
                        },
                "version":"1.0"
               }

        self.send_websocket_request(self.name, data)
