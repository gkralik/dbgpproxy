import asyncore
from dbgpproxy.dispatcher import RegistrationServer, DebugConnectionServer

__author__ = 'gkralik'


class Proxy:
    def __init__(self):
        self._servers = {}

        self._registration_server = RegistrationServer('localhost', 9001, manager=self)
        self._debugger_connection_server = DebugConnectionServer('localhost', 9000, manager=self)

    def start(self):
        asyncore.loop()

    def add_server(self, idekey, host, port, multi):
        if idekey in self._servers:
            return None

        self._servers[idekey] = [[host, port], multi]
        print('add_server: idekey = {}, host = {}, port = {}, multi = {}'.format(idekey, host, port, multi))
        return idekey

    def remove_server(self, idekey):
        if idekey in self._servers:
            print('remove_server: idekey = {}'.format(idekey))
            del self._servers[idekey]
            return idekey

        return None

    def get_server(self, idekey):
        if idekey in self._servers:
            return self._servers[idekey]

        return None
