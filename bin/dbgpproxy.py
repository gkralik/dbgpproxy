import sys
import logging

__author__ = 'gkralik'


def _get_dbgpproxy_lib_path():
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
    sys.path.insert(0, _path)
try:
    try:
        from dbgpproxy.common import *
        from dbgpproxy.dispatcher import *
        from dbgpproxy.proxy import *
    except ImportError:
        pass
finally:
    if _path:
        del sys.path[0]


configure_logging()

if __name__ == "__main__":
    logger = logging.getLogger('dbgpproxy')

    logger.info('starting proxy')
    #Proxy().start()