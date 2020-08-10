"""Module for IQ Option Candles websocket object."""
from pyiqoptionapi.ws.objects.base import Base
from threading import RLock


class Candle(object):
    """Class for IQ Option candle."""

    def __init__(self, candle_data):
        """
        :param candle_data: The list of candles data.
        """
        self.__candle_data = candle_data
        self._lock = RLock()

    @property
    def candle_time(self):
        """Property to get candle time.

        :returns: The candle time.
        """
        with self._lock:
            return self.__candle_data[0]

    @property
    def candle_open(self):
        """Property to get candle open value.

        :returns: The candle open value.
        """
        with self._lock:
            return self.__candle_data[1]

    @property
    def candle_close(self):
        """Property to get candle close value.

        :returns: The candle close value.
        """
        with self._lock:
            return self.__candle_data[2]

    @property
    def candle_high(self):
        """Property to get candle high value.

        :returns: The candle high value.
        """
        with self._lock:
            return self.__candle_data[3]

    @property
    def candle_low(self):
        """Property to get candle low value.

        :returns: The candle low value.
        """
        with self._lock:
            return self.__candle_data[4]

    @property
    def candle_type(self):
        """Property to get candle type value.

        :returns: The candle type value.
        """
        if self.candle_open < self.candle_close:
            return "green"
        elif self.candle_open > self.candle_close:
            return "red"


class Candles(Base):
    """Class for IQ Option Candles websocket object."""

    def __init__(self):
        super(Candles, self).__init__()
        self.__name = "candles"
        self.__candles_data = None
        self._lock = RLock()

    @property
    def candles_data(self):
        """Property to get candles data.

        :returns: The list of candles data.
        """
        with self._lock:
            return self.__candles_data

    @candles_data.setter
    def candles_data(self, candles_data):
        """Method to set candles data."""
        with self._lock:
            self.__candles_data = candles_data

    @property
    def first_candle(self):
        """Method to get first candle.

        :returns: The instance of :class:`Candle
            <iqoptionapi.ws.objects.candles.Candle>`.
        """
        with self._lock:
            return Candle(self.candles_data[0])

    @property
    def second_candle(self):
        """Method to get second candle.

        :returns: The instance of :class:`Candle
            <iqoptionapi.ws.objects.candles.Candle>`.
        """
        with self._lock:
            return Candle(self.candles_data[1])

    @property
    def current_candle(self):
        """Method to get current candle.

        :returns: The instance of :class:`Candle
            <iqoptionapi.ws.objects.candles.Candle>`.
        """
        with self._lock:
            return Candle(self.candles_data[-1])
