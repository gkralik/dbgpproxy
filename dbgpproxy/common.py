import sys
import logging
import dbgpproxy

__author__ = 'gkralik'


log_levels = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARN': logging.WARN,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
}


def configure_logging(level=logging.INFO):
    """
    Set up logging.

    Write to sys.stdout and set log level.
    @param level: The log level.
    """
    logging.basicConfig(stream=sys.stdout, level=level)


if sys.version_info < (3, 2):
    import optparse

    def parse_arguments():
        """
        Parse command line args using optparse (Python version < 3.2).

        @return: List of args.
        """
        parser = optparse.OptionParser(version=dbgpproxy.__version__)
        parser.add_option('-i', type=str, metavar="hostname:port", dest="ide",
                          help="listener port for IDE processes (defaults to 127.0.0.1:9001", default="127.0.0.1:9001")
        parser.add_option('-d', type=str, metavar="hostname:port", dest="dbg",
                          help="listener port for debug processes (defaults to 127.0.0.1:9000",
                          default="127.0.0.1:9000")
        parser.add_option('-l', type=str, metavar="LOGLEVEL", dest="loglevel",
                          help="Log verbosity. Accepted values are CRITICAL, ERROR, WARN, INFO (default), DEBUG",
                          default="INFO")

        return parser.parse_args()[0]
else:
    import argparse

    def parse_arguments():
        """
        Parse command line args using argparse (Python version >= 3.2).

        @return: List of
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--version', action="version", version=dbgpproxy.__version__,
                            help="print version info and exit.")
        parser.add_argument('-i', type=str, metavar="hostname:port", dest="ide",
                            help="listener port for IDE processes (defaults to 127.0.0.1:9001)",
                            default="127.0.0.1:9001")
        parser.add_argument('-d', type=str, metavar="hostname:port", dest="dbg",
                            help="listener port for debug processes (defaults to 127.0.0.1:9000)",
                            default="127.0.0.1:9000")
        parser.add_argument('-l', type=str, metavar="LOGLEVEL", dest="loglevel",
                            help="Log verbosity. Accepted values are CRITICAL, ERROR, WARN, INFO (default), DEBUG",
                            default="INFO")
        return parser.parse_args()