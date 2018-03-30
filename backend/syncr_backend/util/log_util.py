"""Log util functions"""
import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Get a logger with name `name`

    Normally called as `logger = get_logger(__name__)` at the top of a file,
    and then used throughout the file, but `name` can be anything, for example
    for more useful logs for a class might set the class name or maybe even the
    instance __str__

    :param name: The name of the logger. Normally this will be __name__
    :return: A logger that logs to the console
    """
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

    return logger
