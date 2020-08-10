"""Module for base IQ Option base websocket chanel."""


class Base(object):
    """Class for base IQ Option websocket chanel."""

    def __init__(self, api):
        """
        :param api: The instance of :class:`IQOptionAPI
            <iqoptionapi.iqoptionapi.IQOptionAPI>`.
        """
        self.api = api

    def send_websocket_request(self, name, msg, request_id=""):
        """Send request to IQ Option server websocket.
        :param str name: The websocket channel name.
        :param dict msg: The websocket channel msg.
        :returns: The instance of :class:`requests.Response`.
        """
        return self.api.send_websocket_request(name, msg, request_id)
