import logging
import sys

def create_logger(name = __name__, logging_level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(logging_level)

    ch = logging.StreamHandler()
    ch.setLevel(logging_level)

    formatter = logging.Formatter('%(levelname)s:%(name)s - %(message)s')
    ch.setFormatter(formatter)

    # ch = logging.StreamHandler(sys.stdout)
    # ch.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger
