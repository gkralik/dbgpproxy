import asyncore
import logging
from dbgpproxy.dispatcher import RegistrationServer, DebugConnectionServer

__author__ = 'gkralik'


class Proxy:
    def __init__(self, idehost=None, ideport=None, dbghost=None, dbgport=None):
        self.logger = logging.getLogger('dbgpproxy')
        self._servers = {}

        self._registration_server = RegistrationServer(idehost, ideport, dbghost, dbgport, proxy_manager=self)
        self._debugger_connection_server = DebugConnectionServer(dbghost, dbgport, proxy_manager=self)

    @staticmethod
    def start():
        asyncore.loop()

    @staticmethod
    def stop():
        asyncore.close_all()

    def add_server(self, idekey, host, port, multi):
        if idekey in self._servers:
            return None

        self.logger.debug('add_server: idekey = {}, host = {}, port = {}, multi = {}'.format(idekey, host, port, multi))

        self._servers[idekey] = [[host, port], multi]
        return idekey

    def remove_server(self, idekey):
        if idekey in self._servers:
            self.logger.debug('remove_server: idekey = {}'.format(idekey))
            del self._servers[idekey]
            return idekey

        return None

    def get_server(self, idekey):
        if idekey in self._servers:
            return self._servers[idekey]

        return None
