class MissingConfigError(Exception):
    """
    Handles issue of missing config file
    """
    pass


class IncompleteConfigError(Exception):
    """
    Handles issue of incomplete config file
    """
    pass


class UnsupportedOptionError(Exception):
    """
    Handles issue of unsupported store options
    """
    pass
