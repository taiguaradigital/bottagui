

__all__ = ['InstrumentSuspendedError', 'InstrumentExpiredError', 'InstrumentUnsubscribeError']


class InstrumentExpiredError(Exception):
    pass


class InstrumentSuspendedError(Exception):
    pass


class InstrumentUnsubscribeError(Exception):
    pass
