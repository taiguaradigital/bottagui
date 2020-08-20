# -*- coding: utf-8 -*-
import logging


def prepare(mode='INFO'):

    logger = logging.getLogger(__name__)
    if mode == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif mode == 'ERROR':
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(logging.NullHandler())

    websocket_logger = logging.getLogger("websocket")
    if mode == 'DEBUG':
        websocket_logger.setLevel(logging.DEBUG)
    elif mode == 'ERROR':
        websocket_logger.setLevel(logging.ERROR)
    else:
        websocket_logger.setLevel(logging.INFO)
    websocket_logger.addHandler(logging.NullHandler())
