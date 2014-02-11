dbgpproxy
=========

`dbgpproxy` is a simple proxy server for DBGp written with Python.

**Usage:**

    usage: dbgpproxy [-h] [-v] [-i hostname:port] [-d hostname:port] [-l LOGLEVEL]

    optional arguments:
      -h, --help        show this help message and exit
      -v, --version     print version info and exit.
      -i hostname:port  listener port for IDE processes (defaults to
                        127.0.0.1:9001)
      -d hostname:port  listener port for debug processes (defaults to
                        127.0.0.1:9000)
      -l LOGLEVEL       Log verbosity. Accepted values are CRITICAL, ERROR, WARN,
                        INFO (default), DEBUG


Links
-----
[DBGp specification](http://xdebug.org/docs-dbgp.php "DBGp specification")
