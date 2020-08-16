

__all__ = ['InstrumentSuspendedError', 'InstrumentExpiredError', 'InstrumentUnsubscribeError', 'PositionError']


class InstrumentExpiredError(Exception):
    pass


class InstrumentSuspendedError(Exception):
    pass


class InstrumentUnsubscribeError(Exception):
    pass


class PositionError(Exception):
    pass
