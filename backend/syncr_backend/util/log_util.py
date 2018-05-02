"""Log util functions"""
import logging
import os
from typing import Dict  # noqa


loggers = {}  # type: Dict[str, logging.Logger]


def get_logger(name: str) -> logging.Logger:
    """Get a logger with name ``name``

    Normally called as ``logger = get_logger(__name__)`` at the top of a file,
    and then used throughout the file, but ``name`` can be anything, for
    example for more useful logs for a class might set the class name or maybe
    even the instance __str__.

    If the LOG_LEVEL environment variable is set, this will try to set the log
    level to ``os.environ.get('LOG_LEVEL')``.  Defaults to ``INFO``.

    >>> from syncr_backend.util.log_util import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("printing a log line")

    :param name: The name of the logger. Normally this will be __name__
    :return: A logger that logs to the console
    """
    if name in loggers:
        return loggers[name]
    logger = logging.getLogger(name)
    log_level = getattr(
        logging, os.environ.get('LOG_LEVEL', 'INFO').upper(), None,
    )
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    loggers[name] = logger
    return logger
