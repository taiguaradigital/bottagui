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
import queue
import threading
import logging


__all__ = ['deprecated', 'ThreadedMethod', 'never_raise', 'never_raise_return_false']


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""

    def newFunc(*args, **kwargs):
        import warnings
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)

    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc


def never_raise(func):
    """This is a decorator which can be used to mark functions
    as never raise. It will send message error for logging, and return without error for user."""
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            logging.error(err)
    return wrap


def never_raise_return_false(func):
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return False
    return wrap


class ThreadedMethod(object):

    def __init__(self, func):
        self._func = func
        self._threads = {}
        self._queues = {}

    def __get__(self, inst, owner):
        if inst is None:
            return self
        key = self._func.__get__(inst, type(inst))
        if key not in self._queues:
            self._queues[key] = queue.Queue()
            self._threads[key] = threading.Thread(target=self._thread_loop, args=[inst, key])
            self._threads[key].daemon = True
            self._threads[key].start()
        return lambda *a, **k: self._queues[key].put((a, k))

    def _thread_loop(self, inst, key):
        while True:
            args = self._queues[key].get()
            try:
                self._func(inst, *args[0], **args[1])
            except Exception as err:
                logging.error('Error in threaded func %s: %s' % (key.__name__, err))

