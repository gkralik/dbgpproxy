import sys
import logging

__author__ = 'gkralik'
__version__ = '0.5'


def _get_dbgpproxy_lib_path():
    """
    Try to find the dbgproxy lib path.

    Just checks the parent directory for the dbgproxy package.
    @return: The path of the parent directory if the dbgpproxy package is there.
    """
    from os.path import dirname, join, abspath, exists

    try:
        this_dir = dirname(abspath(__file__))
    except NameError:
        this_dir = dirname(abspath(sys.argv[0]))

    parent_dir = dirname(this_dir)

    init_file = join(parent_dir, "dbgpproxy", "__init__.py")
    if exists(init_file):
        return parent_dir


_path = (not hasattr(sys, "frozen") and _get_dbgpproxy_lib_path() or None)
if _path:
    # insert the path
    sys.path.insert(0, _path)
try:
    try:
        from dbgpproxy.common import *
        from dbgpproxy.dispatcher import *
        from dbgpproxy.proxy import *
    except ImportError as e:
        sys.stderr.write('failed to import required modules: %s.\n' % (e))
        sys.exit(3)
finally:
    if _path:
        # delete path again.
        del sys.path[0]


if __name__ == "__main__":
    if sys.version_info < (3, 1):
        exe = sys.executable
        version = '.'.join(map(str, sys.version_info[:3]))
        sys.stderr.write(
            "dbgpproxy must be run with Python version 3.1 or greater. Your current python (%s) is version %s\n" % (
            exe, version))
        sys.exit(2)

    logger = logging.getLogger('dbgpproxy')

    args = parse_arguments()

    # parse IDE host:port
    if not args.ide.find(':'):
        sys.stderr.write('Invalid IDE parameter.\n')
        sys.exit(1)

    idehost, ideport = args.ide.split(':')
    ideport = int(ideport)

    # parse debug host:port
    if not args.dbg.find(':'):
        sys.stderr.write('Invalid debug parameter.\n')
        sys.exit(1)

    dbghost, dbgport = args.dbg.split(':')
    dbgport = int(dbgport)

    # parse log level
    if args.loglevel in log_levels:
        loglevel = log_levels[args.loglevel]
    else:
        sys.stderr.write('Invalid log level.\n')
        sys.exit(1)

    configure_logging(level=loglevel)

    proxy = Proxy(idehost=idehost, ideport=ideport, dbghost=dbghost, dbgport=dbgport)

    try:
        proxy.start()
    except KeyboardInterrupt:
        print('caught CTRL-C, exiting...')
        proxy.stop()
        sys.exit(0)
    except Exception as e:
        logger.critical('Exception: %s' % (e))
        sys.stderr.write('Exception: %s\n' % (e))
        sys.exit(2)
