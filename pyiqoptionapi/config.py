# -*- coding: utf-8 -*-
import logging


def prepare(mode='INFO'):

    logger = logging.getLogger(__name__)
    websocket_logger = logging.getLogger("websocket")

    if mode == 'DEBUG':
        logger.setLevel(logging.DEBUG)
        websocket_logger.setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    elif mode == 'ERROR':
        logger.setLevel(logging.ERROR)
        websocket_logger.setLevel(logging.ERROR)
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(message)s')
    else:
        logger.setLevel(logging.INFO)
        websocket_logger.setLevel(logging.INFO)

    logger.addHandler(logging.NullHandler())
    websocket_logger.addHandler(logging.NullHandler())
